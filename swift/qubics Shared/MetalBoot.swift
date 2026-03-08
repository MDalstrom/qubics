import Metal
import MetalKit
import Cocoa

typealias GameLoopTick = @convention(c) (UnsafeMutableRawPointer) -> Void

var globalTickFunction: GameLoopTick?
var globalCommandQueue: MTLCommandQueue?
var globalViewDelegate: ViewDelegate?
var globalView: MTKView?
var globalDevice: MTLDevice?
var globalLibrary: MTLLibrary?
var globalECSWorld: ECSWorldManager?

class ViewDelegate: NSObject, MTKViewDelegate {
    func draw(in view: MTKView) {
        guard let drawable = view.currentDrawable else { return }
        guard let queue = globalCommandQueue else { return }
        guard let commandBuffer = queue.makeCommandBuffer() else { return }
        
        guard let renderPassDescriptor = view.currentRenderPassDescriptor else { return }
        guard let renderEncoder = commandBuffer.makeRenderCommandEncoder(descriptor: renderPassDescriptor) else { return }
        renderEncoder.endEncoding()
        
        if let tick = globalTickFunction {
            tick(Unmanaged.passUnretained(commandBuffer).toOpaque())
        }
        
        commandBuffer.present(drawable)
        commandBuffer.commit()
    }
    
    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}
}

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }
}

@_cdecl("metal_boot")
public func metal_boot(tickFn: @escaping @convention(c) (UnsafeMutableRawPointer) -> Void) {
    globalTickFunction = tickFn
    
    let app = NSApplication.shared
    app.setActivationPolicy(.regular)
    
    let appDelegate = AppDelegate()
    app.delegate = appDelegate
    
    let menubar = NSMenu()
    let appMenuItem = NSMenuItem()
    menubar.addItem(appMenuItem)
    app.mainMenu = menubar
    
    let appMenu = NSMenu()
    let quitMenuItem = NSMenuItem(title: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
    appMenu.addItem(quitMenuItem)
    appMenuItem.submenu = appMenu
    
    guard let device = MTLCreateSystemDefaultDevice() else { return }
    guard let queue = device.makeCommandQueue() else { return }
    globalCommandQueue = queue
    globalDevice = device
    
    let frame = NSRect(x: 0, y: 0, width: 800, height: 800)
    let window = NSWindow(
        contentRect: frame,
        styleMask: [.titled, .closable, .resizable, .miniaturizable],
        backing: .buffered,
        defer: false
    )
    
    let view = MTKView(frame: frame, device: device)
    view.clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 1)
    view.colorPixelFormat = .bgra8Unorm
    view.preferredFramesPerSecond = 60
    view.depthStencilPixelFormat = .depth32Float_stencil8
    
    let delegate = ViewDelegate()
    globalViewDelegate = delegate
    view.delegate = delegate
    globalView = view
    
    window.contentView = view
    window.center()
    window.makeKeyAndOrderFront(nil)
    
    app.activate(ignoringOtherApps: true)
    app.run()
}

@_cdecl("metal_get_device")
public func metal_get_device() -> UnsafeMutableRawPointer? {
    guard let device = globalDevice else { return nil }
    return Unmanaged.passUnretained(device).toOpaque()
}

@_cdecl("metal_get_view")
public func metal_get_view() -> UnsafeMutableRawPointer? {
    guard let view = globalView else { return nil }
    return Unmanaged.passUnretained(view).toOpaque()
}

@_cdecl("metal_load_library")
public func metal_load_library(path: UnsafePointer<CChar>) -> UnsafeMutableRawPointer? {
    guard let device = globalDevice else { return nil }
    let pathString = String(cString: path)
    let url = URL(fileURLWithPath: pathString)
    guard let library = try? device.makeLibrary(URL: url) else { return nil }
    globalLibrary = library
    return Unmanaged.passUnretained(library).toOpaque()
}

@_cdecl("metal_get_library")
public func metal_get_library() -> UnsafeMutableRawPointer? {
    guard let library = globalLibrary else { return nil }
    return Unmanaged.passUnretained(library).toOpaque()
}

@_cdecl("ecs_load_world")
public func ecs_load_world(ecsLibPath: UnsafePointer<CChar>) -> UnsafeMutableRawPointer? {
    let path = String(cString: ecsLibPath)
    guard let world = ECSWorldManager(libraryPath: path) else { return nil }
    globalECSWorld = world
    return Unmanaged.passUnretained(world).toOpaque()
}

@_cdecl("ecs_get_world_ptr")
public func ecs_get_world_ptr() -> UnsafeMutableRawPointer? {
    guard let worldManager = globalECSWorld else { return nil }
    return UnsafeMutableRawPointer(worldManager.world)
}

@_cdecl("ecs_container_count")
public func ecs_container_count() -> UInt {
    guard let worldManager = globalECSWorld else { return 0 }
    return UInt(worldManager.containerCount())
}

@_cdecl("ecs_get_container")
public func ecs_get_container(index: UInt) -> UnsafeMutableRawPointer? {
    guard let worldManager = globalECSWorld else { return nil }
    guard let container = worldManager.getContainer(index) else { return nil }
    return UnsafeMutableRawPointer(mutating: container)
}
