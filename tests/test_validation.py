from preservationeval import emc, mold, pi


def test_against_javascript(validation):
    """Test Python implementation against JavaScript."""
    differences = validation.run_tests(num_cases=100)

    assert not differences["pi"], "PI calculations differ"
    assert not differences["emc"], "EMC calculations differ"
    assert not differences["mold"], "Mold calculations differ"


def test_specific_cases(test_data_dir):
    """Test specific known cases."""
    # Load saved test cases
    with open(test_data_dir / "test_data.json") as f:
        data = json.load(f)

    for case, expected in zip(data["cases"], data["results"]):
        t, rh = case
        assert pi(t, rh) == expected["pi"]
        assert abs(emc(t, rh) - expected["emc"]) < 1e-6
        assert mold(t, rh) == expected["mold"]
