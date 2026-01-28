from q_engine import hot_reload, bootstrap

def tick_fc():
    from q_engine.bootstrap import get_tick
    return get_tick()
tick, set_tick = hot_reload.dispatch(tick_fc())

def reload(event):
    if not event.src_path.endswith('.py'):
        return
    global tick
    hot_reload.reload(__file__)
    set_tick(tick_fc())
hot_reload.watch(reload)

run = bootstrap.get_run()
run(tick)
