from alt.scenarios.baker import Baker


def get_scenario_baker() -> Baker:
    from alt.scenarios import scenario1
    return scenario1.bake
