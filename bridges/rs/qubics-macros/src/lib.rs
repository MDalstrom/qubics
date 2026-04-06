use proc_macro::TokenStream;
use proc_macro2::TokenStream as TokenStream2;
use quote::quote;
use syn::{
    bracketed,
    parse::{Parse, ParseStream},
    parse_macro_input,
    punctuated::Punctuated,
    ItemFn, Token, Type,
};

fn fnv1a_hash(bytes: &[u8]) -> u32 {
    const FNV_OFFSET: u32 = 2166136261;
    const FNV_PRIME: u32 = 16777619;
    bytes.iter().fold(FNV_OFFSET, |hash, &b| {
        hash.wrapping_mul(FNV_PRIME) ^ b as u32
    })
}

fn type_to_descriptor(ty: &Type) -> TokenStream2 {
    let id = fnv1a_hash(quote!(#ty).to_string().as_bytes());
    quote! {
        ::qubics::ComponentMeta {
            id: #id,
            stride: ::std::mem::size_of::<#ty>(),
        }
    }
}

struct ComponentArgs {
    reads: Vec<Type>,
    writes: Vec<Type>,
}

impl Parse for ComponentArgs {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let mut reads = vec![];
        let mut writes = vec![];

        while !input.is_empty() {
            let name: syn::Ident = input.parse()?;
            input.parse::<Token![=]>()?;
            let content;
            bracketed!(content in input);
            let types: Punctuated<Type, Token![,]> =
                content.parse_terminated(Type::parse, Token![,])?;

            match name.to_string().as_str() {
                "reads" => reads = types.into_iter().collect(),
                "writes" => writes = types.into_iter().collect(),
                other => {
                    return Err(syn::Error::new(
                        name.span(),
                        format!("unknown key `{other}`, expected `reads` or `writes`"),
                    ))
                }
            }

            if input.peek(Token![,]) {
                input.parse::<Token![,]>()?;
            }
        }

        Ok(ComponentArgs { reads, writes })
    }
}

#[proc_macro_attribute]
pub fn bake(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let func = parse_macro_input!(item as ItemFn);
    let func_name = &func.sig.ident;
    let vis = &func.vis;
    let wrapper_name = quote::format_ident!("__bake_c_{}", func_name);
    let registration_name = quote::format_ident!("__bake_registration_{}", func_name);

    quote! {
        #func

        unsafe extern "C" fn #wrapper_name(__world: *mut ::qubics::WorldApi) {
            #func_name(*__world)
        }

        #[::linkme::distributed_slice(::qubics::BAKE_SYSTEMS)]
        #[linkme(crate = ::linkme)]
        #[allow(non_upper_case_globals)]
        #vis static #registration_name: ::qubics::BakeEntry = ::qubics::BakeEntry {
            run: #wrapper_name,
        };
    }
    .into()
}

fn staged_macro(
    attr: TokenStream,
    item: TokenStream,
    slice: TokenStream2,
    entry_type: TokenStream2,
    prefix: &str,
) -> TokenStream {
    let args = parse_macro_input!(attr as ComponentArgs);
    let func = parse_macro_input!(item as ItemFn);
    let func_name = &func.sig.ident;
    let vis = &func.vis;

    let reads: Vec<TokenStream2> = args.reads.iter().map(type_to_descriptor).collect();
    let writes: Vec<TokenStream2> = args.writes.iter().map(type_to_descriptor).collect();
    let reads_len = reads.len();
    let writes_len = writes.len();
    let registration_name = quote::format_ident!("__{}_registration_{}", prefix, func_name);

    quote! {
        #func

        #[::linkme::distributed_slice(#slice)]
        #[linkme(crate = ::linkme)]
        #[allow(non_upper_case_globals)]
        #vis static #registration_name: #entry_type = {
            static READS: [::qubics::ComponentMeta; #reads_len] = [#(#reads),*];
            static WRITES: [::qubics::ComponentMeta; #writes_len] = [#(#writes),*];
            #entry_type {
                run: #func_name,
                reads: &READS,
                writes: &WRITES,
            }
        };
    }
    .into()
}

#[proc_macro_attribute]
pub fn simulate(attr: TokenStream, item: TokenStream) -> TokenStream {
    staged_macro(
        attr,
        item,
        quote!(::qubics::SIMULATION_SYSTEMS),
        quote!(::qubics::SimulationEntry),
        "simulate",
    )
}

#[proc_macro_attribute]
pub fn render(attr: TokenStream, item: TokenStream) -> TokenStream {
    staged_macro(
        attr,
        item,
        quote!(::qubics::RENDER_SYSTEMS),
        quote!(::qubics::RenderEntry),
        "render",
    )
}
