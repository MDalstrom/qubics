use qubics_sys::ComponentDescriptor;

pub trait Component: Sized + 'static {
    fn descriptor() -> &'static ComponentDescriptor;
}
