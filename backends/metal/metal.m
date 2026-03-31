#import "contract.h"
#import <Cocoa/Cocoa.h>
#import <MetalKit/MetalKit.h>
#import <signal.h>

static void signal_handler(int sig) {
    [NSApp terminate:nil];
}

@interface MetalGameLoop : NSObject <MTKViewDelegate, NSWindowDelegate>

@property (nonatomic, strong) NSWindow *window;
@property (nonatomic, strong) MTKView *mtkView;
@property (nonatomic, strong) id<MTLDevice> device;
@property (nonatomic, strong) id<MTLCommandQueue> commandQueue;
@property (nonatomic, assign) tick_function tick_fn;

- (id)initWithTickFunction:(tick_function)tick_fn;
- (void)run;

@end

@implementation MetalGameLoop

- (id)initWithTickFunction:(tick_function)tick_fn {
    self = [super init];
    if (self) {
        self.tick_fn = tick_fn;
        
        NSRect frame = NSMakeRect(0, 0, 800, 600);
        
        self.window = [[NSWindow alloc]
            initWithContentRect:frame
            styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable
            backing:NSBackingStoreBuffered
            defer:NO];
        [self.window setTitle:@"Qubics"];
        [self.window center];
        [self.window setDelegate:self];

        self.device = MTLCreateSystemDefaultDevice();
        self.mtkView = [[MTKView alloc] initWithFrame:frame device:self.device];
        self.mtkView.delegate = self;
        
        self.window.contentView = self.mtkView;
        
        self.commandQueue = [self.device newCommandQueue];
    }
    return self;
}

- (void)run {
    [self.window makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];
    [NSApp run];
}

- (void)mtkView:(MTKView *)view drawableSizeWillChange:(CGSize)size {
}

- (BOOL)windowShouldClose:(NSWindow *)sender {
    [NSApp terminate:nil];
    return YES;
}

- (void)drawInMTKView:(MTKView *)view {
    typedef struct {
        void* mtkView;
        void* device;
        void* commandQueue;
    } RenderContext;
    
    RenderContext context;
    context.mtkView = (__bridge void*)self.mtkView;
    context.device = (__bridge void*)self.device;
    context.commandQueue = (__bridge void*)self.commandQueue;
    
    if (self.tick_fn) {
        self.tick_fn(&context);
    }
    
    id<MTLCommandBuffer> commandBuffer = [self.commandQueue commandBuffer];
    MTLRenderPassDescriptor *renderPassDescriptor = view.currentRenderPassDescriptor;
    
    if (renderPassDescriptor != nil) {
        id<MTLRenderCommandEncoder> renderEncoder = [commandBuffer renderCommandEncoderWithDescriptor:renderPassDescriptor];
        [renderEncoder endEncoding];
        
        [commandBuffer presentDrawable:view.currentDrawable];
    }
    
    [commandBuffer commit];
}

@end

void run(tick_function tick_fn) {
    @autoreleasepool {
        signal(SIGINT, signal_handler);
        
        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];
        
        NSImage *appIcon = [NSApp applicationIconImage];
        if (!appIcon) {
            appIcon = [NSImage imageNamed:NSImageNameApplicationIcon];
            [NSApp setApplicationIconImage:appIcon];
        }
        
        NSMenuItem *quitItem = [[NSMenuItem alloc] initWithTitle:@"Quit" 
                                                          action:@selector(terminate:) 
                                                   keyEquivalent:@"q"];
        NSMenu *appMenu = [[NSMenu alloc] init];
        [appMenu addItem:quitItem];
        
        NSMenuItem *appMenuItem = [[NSMenuItem alloc] init];
        [appMenuItem setSubmenu:appMenu];
        
        NSMenu *menuBar = [[NSMenu alloc] init];
        [menuBar addItem:appMenuItem];
        [NSApp setMainMenu:menuBar];
        
        [NSApp finishLaunching];
        
        MetalGameLoop *delegate = [[MetalGameLoop alloc] initWithTickFunction:tick_fn];
        
        [delegate run];
    }
}
