from src.alt import hot_reload, bootstrap

def tick_fc():
    from src.alt.soft_body import tick
    return tick
tick = tick_fc()

def reload(event):
    if not event.src_path.endswith('.py'):
        return
    global tick
    hot_reload.reload(__file__)
    tick = tick_fc()
hot_reload.watch(reload)

def dispatch(*args, **kwargs):
    global tick
    try:
        tick(*args, **kwargs)
    except Exception as e:
        import traceback
        traceback.print_exception(e)

run = bootstrap.get_run()
run(dispatch)
