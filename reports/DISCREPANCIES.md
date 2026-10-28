_Generated on 2026-10-28 00:27:20 UTC against midea-local 14.0.0_

# Discrepancies review

Every `MISSING` / `DIFFERENT` finding of [`REPORT.md`](REPORT.md), sorted into a category by rule and merged over the Lua files of each device type. Decisions recorded in `midea_lua_conformance/triage.py` override the rule and are marked **recorded**; add one there and regenerate to record a new decision.

Run scope: 166 comparisons. Totals — MATCH 524, MISSING 267, DIFFERENT 42, UNKNOWN 6876; 286 distinct findings reviewed below.

## A. Likely genuine midealocal bugs or gaps — worth an issue/PR

| device | finding | Lua | midealocal | Lua files | why |
| --- | --- | --- | --- | --- | --- |
| `b0` | enum `mode[0x02]` | 0x02 -> 'baking' | - | 1 | the Lua defines a value midealocal has no name for |
| `b1` | enum `status[0xFF]` | 0xFF -> 'none' | - | 1 | the Lua defines a value midealocal has no name for |
| `b4` | enum `status[0x07]` | 0x07 -> 'save_power' | - | 1 | the Lua defines a value midealocal has no name for |
| `b4` | enum `status[0x08]` | 0x08 -> 'preheating' | - | 1 | the Lua defines a value midealocal has no name for |
| `b4` | enum `status[0x0A]` | 0x0A -> 'lock_off' | - | 1 | the Lua defines a value midealocal has no name for |
| `b4` | enum `status[0x11]` | 0x11 -> 'finish' | - | 1 | the Lua defines a value midealocal has no name for |
| `b4` | enum `status[0x66]` | 0x66 -> 'recipes_finish' | - | 1 | the Lua defines a value midealocal has no name for |
| `b4` | enum `status[0x88]` | 0x88 -> 'preheat_finish' | - | 1 | the Lua defines a value midealocal has no name for |
| `e1` | enum `status[0x04]` | `cancel_order` | `error` | 1 | **recorded:** cancel_order vs error is a real divergence worth a look. |
| `fb` | enum `mode[0x00]` | 0x00 -> 'humidity_invalid' | - | 1 | the Lua defines a value midealocal has no name for |
| `fb` | enum `mode[0x09]` | 0x09 -> 'custom' | - | 1 | the Lua defines a value midealocal has no name for |
| `fb` | enum `mode[0x20]` | 0x20 -> 'humidity_const' | - | 1 | the Lua defines a value midealocal has no name for |
| `fb` | enum `mode[0x30]` | 0x30 -> 'humidity_one' | - | 1 | the Lua defines a value midealocal has no name for |
| `fb` | enum `mode[0x40]` | 0x40 -> 'humidity_two' | - | 1 | the Lua defines a value midealocal has no name for |
| `fb` | enum `mode[0x50]` | 0x50 -> 'humidity_three' | - | 1 | the Lua defines a value midealocal has no name for |

## B. Different logical vocabulary — probably intentional

| device | finding | Lua | midealocal | Lua files | why |
| --- | --- | --- | --- | --- | --- |
| `b0` | enum `mode[0x43]` | `fast_baking` | `baking` | 1 | same protocol value, different name |
| `b0` | enum `status[0x02]` | `work` | `idle` | 1 | same protocol value, different name |
| `b0` | enum `status[0x03]` | `pause` | `working` | 1 | same protocol value, different name |
| `b0` | enum `status[0x04]` | `end` | `finished` | 1 | same protocol value, different name |
| `b0` | enum `status[0x09]` | `three_sec` | `three` | 1 | same protocol value, different name |
| `b1` | enum `status[0x01]` | `cancel` | `standby` | 1 | same protocol value, different name |
| `b1` | enum `status[0x02]` | `work` | `idle` | 1 | same protocol value, different name |
| `b1` | enum `status[0x03]` | `pause` | `working` | 1 | same protocol value, different name |
| `b1` | enum `status[0x04]` | `end` | `finished` | 1 | same protocol value, different name |
| `b1` | enum `status[0x06]` | `appointment` | `paused` | 1 | same protocol value, different name |
| `b4` | enum `status[0x02]` | `work` | `idle` | 1 | same protocol value, different name |
| `b4` | enum `status[0x05]` | `lock_on` | `delay` | 1 | same protocol value, different name |
| `e1` | enum `mode[0x00]` | `neutral_gear` | `none` | 1 | **recorded:** neutral_gear -> none is a known intentional rename. |
| `e1` | enum `mode[0x09]` | `self_define` | `90min` | 1 | same protocol value, different name |
| `e1` | enum `status[0x00]` | `power_off` | `off` | 1 | same protocol value, different name |
| `e1` | enum `status[0x02]` | `order` | `delay` | 1 | same protocol value, different name |
| `e1` | enum `status[0x03]` | `work` | `running` | 1 | same protocol value, different name |
| `fb` | enum `mode[0x01]` | `intelligent` | `auto` | 1 | same protocol value, different name |
| `fb` | enum `mode[0x02]` | `efficient` | `eco` | 1 | same protocol value, different name |
| `fb` | enum `mode[0x08]` | `fast_hot` | `fast_heating` | 1 | same protocol value, different name |
| `fb` | enum `mode[0x10]` | `humidity_close` | `standby` | 1 | same protocol value, different name |

## C. Byte-offset shifts — needs a protocol expert per device

| device | shift (midealocal - Lua) | fields | why |
| --- | --- | --- | --- |
| `ac` | +13 | `swing_lr` 7→20 | read from a different byte |
| `b6` | -3 / -1 | `light` 4→1, `power` 3→2 | read from a different byte |
| `cd` | +19 | `water_pump` 8→27 | read from a different byte |
| `da` | +18 / +1 | `error_code` 6→24, `program` 3→4 | read from a different byte |
| `db` | +1 | `mode` 2→3, `program` 3→4 | read from a different byte |
| `fc` | +10 | `anion` 9→19 | read from a different byte |

## D. Mask/bit differences on the same byte

| device | finding | Lua | midealocal | Lua files | why |
| --- | --- | --- | --- | --- | --- |
| `a1` | decode_field `fan_speed` | `byte[3] & 0xFF >> 0` | `byte[3] & 0x7F >> 0` | 1 | same byte, different mask or shift |
| `cd` | decode_field `power` | `byte[2] & 0xFF >> 0` | `byte[2] & 0x01 >> 0` | 1 | **recorded:** Lua reads the whole byte, midealocal masks the high bits; midealocal is arguably more correct, low risk. |
| `fb` | decode_field `power` | `byte[0] & 0xFF >> 0` | `byte[0] & 0x01 >> 0` | 1 | **recorded:** Lua reads the whole byte, midealocal masks the high bits; midealocal is arguably more correct, low risk. |
| `fd` | decode_field `fan_speed` | `byte[3] & 0xFF >> 0` | `byte[3] & 0x7F >> 0` | 1 | **recorded:** Lua reads the whole byte, midealocal masks the high bits; midealocal is arguably more correct, low risk. |

## E. Framework false positives / known limitations (do not act on these)

**recorded:** timer-packing scratch variable in the Lua, not a device attribute.

- `ac` (6): `close_hour`, `close_step_mintues`, `open_hour`, `open_step_mintues`, `ptc`, `small_temperature`

_midealocal exposes this attribute, but the framework cannot see where it is parsed_

- `ac` (1): `error_code`
- `ca` (1): `variable_mode`
- `e2` (1): `error_code`
- `fa` (7): `anion`, `anophelifuge`, `body_feeling_scan`, `error_code`, `mode`, `scene`, `voice`
- `x13` (3): `brightness`, `color_temperature`, `power`

**recorded:** Lua reads it from a different byte per dataType and midealocal has several body classes; only one branch is captured on each side.

- `ac` (2): `indoor_temperature`, `outdoor_temperature`

_same bits: whole byte >> N vs (byte & top bits) >> N_

- `da` (3): `dehydration_speed`, `dehydration_time`, `rinse_level`

## F. Coverage gaps (UNKNOWN, not discrepancies)

UNKNOWN findings (not auto-verifiable) by area: decode_field 6409, enum 15, extractor 149, framing 24, identity 118, introspection 161

- 16 Lua device types have no midealocal package: `b2` `b7` `c1` `d9` `e7` `e9` `eb` `ef` `f1` `x10` `x14` `x17` `x51` `x70` `x9a` `x9b`
- 4 midealocal packages have no Lua: `ad` `c2` `ce` `x34`

## G. Requests the Lua builds that midealocal never sends

- `ac` (1): `body_type 0x01`
- `b1` (4): `body_type 0x22`, `body_type 0x23`, `body_type 0x24`, `body_type 0x26`
- `b4` (2): `body_type 0x04`, `body_type 0x22`
- `cf` (1): `body_type 0x07`
- `fa` (1): `body_type 0x00`
- `x13` (13): `body_type 0x01`, `body_type 0x02`, `body_type 0x03`, `body_type 0x04`, `body_type 0x05`, `body_type 0x06`, `body_type 0x07`, `body_type 0x08`, `body_type 0x09`, `body_type 0x31`, `body_type 0x32`, `body_type 0x33`, `body_type 0x34`
- `x26` (1): `body_type 0x03`
- `x40` (1): `body_type 0x03`

## H. Fields the Lua reads that midealocal does not parse

- `a1` (1): `tank_status`
- `ac` (2): `strong_wind`, `temperature`
- `b0` (1): `second`
- `b1` (7): `cur_temp`, `error_code`, `hour`, `lock`, `minutes`, `temperature`, `workstatus`
- `b6` (3): `error_code`, `gear`, `intelligent`
- `ca` (55): `acme_freezing_mode`, `acquire_icea_mode`, `acquire_water_mode`, `all_icea_status`, `bar_door_power`, `beef`, `brash_icea_mode`, `chicken`, `duck_meat`, `dumplings`, `fast_cold_minute_high`, `fast_cold_minute_low`, `fast_freeze_minute_high`, `fast_freeze_minute_low`, `fish`, `food_site`, `freezing_door_power`, `freezing_fahrenheit`, `freezing_power`, `freezing_real_temperature`, `freezing_temperature`, `function_switch`, `glue_pudding`, `human_induction`, `ice_cream`, `ice_machine_power`, `ice_machine_water_status`, `ice_mouth_power`, `iced_mode`, `interval_room_temperature_level`, `is_error`, `l_variable_real_temperature`, `l_variable_temperature`, `leach_expire_day`, `milk_mode`, `moisturize_mode`, `motor_deicing_status`, `motor_reset_status`, `mutton`, `performance_mode`, `plasma_aseptic_mode`, `pork`, `power_consumption_high`, `power_consumption_low`, `preservation_mode`, `r_variable_real_temperature`, `r_variable_temperature`, `radar_mode`, `refrigeration_door_power`, `refrigeration_fahrenheit`, `refrigeration_real_temperature`, `refrigeration_temperature`, `shrimp`, `unfreeze`, `variable_door_power`
- `cd` (33): `backwater_effect`, `compatibilizing_mode`, `compressor`, `control_type`, `defrost`, `dicaryon_heat`, `energy_mode`, `four_way_valve`, `high_wind`, `low_wind`, `middle_wind`, `mute`, `open_ptc_temp`, `order1_temp`, `order1_time_hour`, `order1_time_min`, `order2_temp`, `order2_time_hour`, `order2_time_min`, `refrigerant_recycling`, `smart_effect`, `standard_mode`, `sterilize_effect`, `timer1_close_hour`, `timer1_close_min`, `timer1_effect`, `timer1_open_hour`, `timer1_open_min`, `timer2_close_hour`, `timer2_close_min`, `timer2_effect`, `timer2_open_hour`, `timer2_open_min`
- `da` (2): `mode`, `temperature`
- `db` (4): `byte13`, `error_code`, `expert_step`, `soak_count`
- `e2` (6): `end_time_minute`, `heat`, `mode_value1`, `mode_value2`, `mode_value3`, `safe`
- `e3` (4): `byte13`, `byte14`, `byte18`, `change_litre`
- `e8` (8): `power`, `stage1`, `stage1_time`, `stage2`, `stage2_time`, `stage3`, `stage3_time`, `stage_all_time`
- `ea` (18): `left_min`, `mouth_feel`, `order_hour`, `order_min`, `rice_cup_number`, `rice_level`, `rice_type`, `step_actual_time`, `step_expect_time`, `storage_expect_cup`, `storage_humodity`, `storage_temp`, `storage_type`, `storage_volume_level`, `voltage`, `warm_min`, `work_flag`, `work_stage`
- `ed` (8): `byte12`, `byte13`, `byte14`, `byte15`, `cool_temp`, `error_code`, `heat_temp`, `life4`
- `fa` (13): `gear`, `hum_feedback`, `humidity`, `lock`, `sleep_sensor`, `temp_feedback`, `temperature`, `timer_off_hour`, `timer_off_minute_bit`, `timer_off_minute_ten`, `timer_on_hour`, `timer_on_minute_bit`, `timer_on_minute_ten`
- `fb` (1): `lock`
- `fc` (6): `ash_tvoc`, `error_code`, `hour`, `humidify_mode`, `pm25_high`, `step_mintues`
- `fd` (1): `error_code`
- `x13` (16): `cmd_type`, `color_blue`, `color_green`, `color_red`, `delay_light_off`, `film_brightness`, `film_color_temperature`, `life_brightness`, `life_color_temperature`, `light_brightness`, `light_color_temperature`, `mild_brightness`, `mild_color_temperature`, `read_brightness`, `read_color_temperature`, `scene_light`

## Resolved since the last review

Recorded decisions whose finding no longer appears; delete them from `triage.py` once confirmed.

- `b0` decode_field `status`: b0 status/mode parsing is broadly out of step with T_0000_B0_6.lua (Lua: status = byte[0] & 0x7F, mode = byte[1]); needs a full re-read.
- `b0` decode_field `mode`: b0 status/mode parsing is broadly out of step with T_0000_B0_6.lua (Lua: status = byte[0] & 0x7F, mode = byte[1]); needs a full re-read.
- `ea` decode_field `top_temperature`: +40 is large and suspicious; start the offset review here.
- `ea` decode_field `bottom_temperature`: +40 is large and suspicious; start the offset review here.
