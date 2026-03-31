use proc_macro::TokenStream;
use proc_macro2::Span;
use quote::quote;
use syn::{
    parse::{Parse, ParseStream},
    parse_macro_input,
    punctuated::Punctuated,
    DeriveInput, Ident, ItemFn, Token,
};

// ---------------------------------------------------------------------------
// #[derive(Component)]
// ---------------------------------------------------------------------------

/// Generates a `'static` `ComponentDescriptor` and implements `Component`.
///
/// The static is named `__COMP_{TypeName}` and is referenced by `#[system]`.
#[proc_macro_derive(Component)]
pub fn derive_component(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    let name_str = name.to_string();
    let static_ident = Ident::new(&format!("__COMP_{name}"), Span::call_site());

    quote! {
        #[allow(non_upper_case_globals)]
        static #static_ident: ::qubics::reexport::ComponentDescriptor =
            ::qubics::reexport::ComponentDescriptor {
                stride: ::std::mem::size_of::<#name>(),
                // SAFETY: string literal is 'static and null-terminated.
                name: concat!(#name_str, "\0").as_ptr() as *const ::std::ffi::c_char,
            };

        impl ::qubics::Component for #name {
            fn descriptor() -> &'static ::qubics::reexport::ComponentDescriptor {
                &#static_ident
            }
        }
    }
    .into()
}

// ---------------------------------------------------------------------------
// #[system(reads = [A, B], writes = [C])]
// ---------------------------------------------------------------------------

struct SystemArgs {
    reads: Vec<Ident>,
    writes: Vec<Ident>,
}

impl Parse for SystemArgs {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let mut reads = Vec::new();
        let mut writes = Vec::new();

        while !input.is_empty() {
            let key: Ident = input.parse()?;
            let _: Token![=] = input.parse()?;

            let content;
            syn::bracketed!(content in input);
            let types: Punctuated<Ident, Token![,]> =
                content.parse_terminated(Ident::parse, Token![,])?;

            match key.to_string().as_str() {
                "reads" => reads.extend(types),
                "writes" => writes.extend(types),
                other => {
                    return Err(syn::Error::new(
                        key.span(),
                        format!("unknown key `{other}`, expected `reads` or `writes`"),
                    ))
                }
            }

            if input.peek(Token![,]) {
                let _: Token![,] = input.parse()?;
            }
        }

        Ok(SystemArgs { reads, writes })
    }
}

/// Wraps a system function into a C-compatible trampoline and registers it
/// with `inventory` so `qubics_plugin` picks it up automatically.
///
/// ```rust
/// #[system(reads = [Position], writes = [Velocity])]
/// fn my_system(world: *mut std::ffi::c_void) { ... }
/// ```
#[proc_macro_attribute]
pub fn system(attr: TokenStream, item: TokenStream) -> TokenStream {
    let args = parse_macro_input!(attr as SystemArgs);
    let func = parse_macro_input!(item as ItemFn);

    let fn_name = &func.sig.ident;
    let trampoline_ident =
        Ident::new(&format!("__trampoline_{fn_name}"), Span::call_site());
    let reads_ident = Ident::new(&format!("__READS_{fn_name}"), Span::call_site());
    let writes_ident = Ident::new(&format!("__WRITES_{fn_name}"), Span::call_site());

    let reads_statics: Vec<_> = args
        .reads
        .iter()
        .map(|t| {
            let s = Ident::new(&format!("__COMP_{t}"), Span::call_site());
            quote! { &#s }
        })
        .collect();

    let writes_statics: Vec<_> = args
        .writes
        .iter()
        .map(|t| {
            let s = Ident::new(&format!("__COMP_{t}"), Span::call_site());
            quote! { &#s }
        })
        .collect();

    let reads_len = reads_statics.len();
    let writes_len = writes_statics.len();

    quote! {
        #func

        #[allow(non_upper_case_globals)]
        static #reads_ident: [&'static ::qubics::reexport::ComponentDescriptor; #reads_len] =
            [ #(#reads_statics),* ];

        #[allow(non_upper_case_globals)]
        static #writes_ident: [&'static ::qubics::reexport::ComponentDescriptor; #writes_len] =
            [ #(#writes_statics),* ];

        unsafe extern "C" fn #trampoline_ident(
            world: *mut ::std::ffi::c_void,
            _ctx: *mut ::std::ffi::c_void,
        ) {
            #fn_name(world);
        }

        ::qubics::inventory::submit! {
            ::qubics::system::SystemRegistration {
                trampoline: #trampoline_ident,
                reads: &#reads_ident,
                writes: &#writes_ident,
            }
        }
    }
    .into()
}
