from automation import plugins


def test_exact_name_outscores_substring():
    assert plugins.match_score("Pro-Q 4", "Pro-Q 4") == 1000
    assert plugins.match_score("Pro-Q 4", "Pro") >= 900


def test_vendor_path_makes_vendor_query_match():
    plugin = {"name": "Pro-L 2", "path": "plugins/FabFilter/Pro-L 2"}
    assert plugins.match_score(plugins.plugin_haystack(plugin), "FabFilter Pro-L 2") >= 700


def test_single_char_token_does_not_false_match():
    pro_l = {"name": "Pro-L 2", "path": "plugins/FabFilter/Pro-L 2"}
    pro_r = {"name": "Pro-R 2", "path": "plugins/FabFilter/Pro-R 2"}
    q = "FabFilter Pro-L 2"
    s_l = max(plugins.match_score(pro_l["name"], q), plugins.match_score(plugins.plugin_haystack(pro_l), q))
    s_r = max(plugins.match_score(pro_r["name"], q), plugins.match_score(plugins.plugin_haystack(pro_r), q))
    assert s_l > s_r
    assert s_r == 0
