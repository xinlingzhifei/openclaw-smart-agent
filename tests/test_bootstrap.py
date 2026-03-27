def test_package_version_is_importable():
    import openclaw_smart_agent

    assert openclaw_smart_agent.__version__ == "0.1.0"
