"""Provider Template A2UI 画廊数据集测试。"""

from __future__ import annotations

import json
from collections import Counter

from services.template_generation.engine.cardplan.preview_dataset import (
    build_template_preview_cases,
    validate_preview_asset_paths,
    write_template_preview_dataset,
)


def test_template_preview_dataset_covers_all_business_templates(tmp_path):
    manifest = write_template_preview_dataset(tmp_path)
    cases = manifest["cases"]

    assert manifest["templateCount"] == 88
    assert manifest["countsByLayout"] == {
        "Support": 19,
        "Compact": 17,
        "Hero": 18,
        "Full": 20,
        "WideHero": 2,
        "WideFull": 12,
    }
    assert manifest["countsBySize"] == {"2x2": 74, "2x4": 14}
    assert len(cases) == 88
    assert len({case["templateId"] for case in cases}) == 88
    assert all((tmp_path / case["file"]).is_file() for case in cases)


def test_template_preview_a2ui_has_surface_components_and_data():
    cases = build_template_preview_cases()

    for case in cases:
        assert len(case.messages) == 3
        assert "createSurface" in case.messages[0]
        assert "updateComponents" in case.messages[1]
        assert "updateDataModel" in case.messages[2]
        components = case.messages[1]["updateComponents"]["components"]
        root = next(component for component in components if component["id"] == "root")
        assert root["component"] == "Column"
        slot = next(component for component in components if component["id"] == "root_0")
        assert slot["styles"]["height"] == case.content_height_vp


def test_bluetooth_battery_status_wide_full_matches_q048_visual_contract():
    case = next(
        item
        for item in build_template_preview_cases()
        if item.template_id == "BluetoothDeviceOverviewBatteryStatusWideFull@1"
    )

    assert case.layout_kind == "WideFull"
    assert case.size == "2x4"
    assert case.content_height_vp == 136
    assert case.primary_data == ("/isConnected",)
    assert case.secondary_data == (
        "/batteryLevel",
        "/leftBatteryLevel",
        "/rightBatteryLevel",
    )
    components = case.messages[1]["updateComponents"]["components"]
    component_by_id = {component["id"]: component for component in components}
    assert component_by_id["root_0_0_0"]["styles"]["height"] == 48
    title = component_by_id["root_0_0_0_0_0"]
    assert title["content"] == ""
    assert title["styles"]["height"] == 16
    assert title["styles"]["fontSize"] == 12
    connection = component_by_id["root_0_0_0_1"]
    assert connection["styles"]["height"] == 24
    assert connection["styles"]["fontSize"] == 18
    battery_row = component_by_id["root_0_0_1"]
    assert battery_row["styles"]["height"] == 34
    assert battery_row["styles"]["justifyContent"] == "center"
    assert battery_row["itemMargin"] == 10
    assert [component_by_id[f"root_0_0_1_{index}"]["styles"]["width"] for index in range(3)] == [
        32,
        32,
        32,
    ]
    assert [component_by_id[f"root_0_0_1_{index}_1"]["content"] for index in range(3)] == [
        "{{ '' + ${/data/earphone/leftBatteryLevel} + '%' }}",
        "{{ '' + ${/data/earphone/rightBatteryLevel} + '%' }}",
        "{{ '' + ${/data/earphone/batteryLevel} + '%' }}",
    ]
    assert all(
        component_by_id[f"root_0_0_1_{index}_1"]["styles"]["fontSize"] == 8
        for index in range(3)
    )
    used_height = 48 + 30 + 34
    assert case.content_height_vp - used_height == 24
    data_model = case.messages[2]["updateDataModel"]["value"]["data"]["earphone"]
    assert set(data_model) == {
        "isConnected",
        "batteryLevel",
        "leftBatteryLevel",
        "rightBatteryLevel",
    }


def test_template_preview_assets_are_bundled_by_genui_evaluation():
    cases = build_template_preview_cases()
    paths = validate_preview_asset_paths(cases)
    names = {path.rsplit("/", 1)[-1] for path in paths}

    assert names == {
        "battery_leaf_fill.svg",
        "calendar_fill.svg",
        "clock_fill.svg",
        "earphone_case_16644.svg",
        "externaldrive_fill.svg",
        "figure_run.svg",
        "flame_fill.svg",
        "heart_fill.svg",
        "icon_earphone.svg",
        "icon_tiktok.png",
        "icon_weather1.svg",
        "l_circle_fill.svg",
        "location_north_up_right_fill.svg",
        "moon_z_fill_1.svg",
        "r_circle_fill.svg",
    }


def test_template_preview_manifest_data_tiers_are_disjoint():
    cases = build_template_preview_cases()

    for case in cases:
        counts = Counter((*case.primary_data, *case.secondary_data, *case.optional_data))
        assert all(count == 1 for count in counts.values())
        assert case.primary_data
        assert json.dumps(case.messages, ensure_ascii=False)


def test_earphone_hero_uses_title_parameter_without_title_binding():
    case = next(
        item
        for item in build_template_preview_cases()
        if item.template_id == "BluetoothDeviceOverviewHero@1"
    )

    assert case.primary_data == ("/isConnected", "/earphoneName")
    assert case.secondary_data == ("/leftBatteryLevel", "/rightBatteryLevel")
    assert case.optional_data == ()
    assert "已连接" in json.dumps(case.messages, ensure_ascii=False)
    data_model = case.messages[2]["updateDataModel"]["value"]["data"]["earphone"]
    assert set(data_model) == {
        "isConnected",
        "earphoneName",
        "leftBatteryLevel",
        "rightBatteryLevel",
    }
