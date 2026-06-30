# WL527 Requirements Atom Table

Mechanical format:

| Atom ID | Requirement | Locator | Expected | Verdict |
|---|---|---|---|---|
| Audio setting #1.a | Noise Control function exists. | `audio-settings::noise-control` | `function "Noise Control"` | pass |
| Audio setting #1.b | Noise Control has modes ANC, Transparency, and Off. | `audio-settings::noise-control::options` | `anc, transparency, off` | pass |
| Audio setting #1.c | ANC is selected by default. | `audio-settings::noise-control::option(anc).selected` | `true` | pass |
| Audio setting #1.d | ANC reveals Adaptive ANC. | `audio-settings::noise-control::reveals.anc` | `toggle "Adaptive ANC"` | pass |
| Audio setting #1.e | Adaptive ANC has the required tooltip. | `audio-settings::noise-control::reveals.anc.component(adaptive-anc).info` | `Automatically adjusts Active Noise Cancellation levels based on your surroundings` | pass |
| Audio setting #1.f | Transparency reveals Transparency Strength. | `audio-settings::noise-control::reveals.transparency` | `slider "Transparency Strength"` | pass |
| Audio setting #1.g | Transparency Strength starts at Low/1. | `audio-settings::noise-control::reveals.transparency.component(transparency-strength).min` | `1` | pass |
| Audio setting #1.h | Transparency Strength reaches Max/3. | `audio-settings::noise-control::reveals.transparency.component(transparency-strength).max` | `3` | pass |
| Audio setting #1.i | Transparency Strength has 3 stops. | `audio-settings::noise-control::reveals.transparency.component(transparency-strength).stops` | `3` | pass |
| Audio setting #2.a | Collaboration function exists. | `audio-settings::collaboration` | `function "Collaboration"` | pass |
| Audio setting #2.b | Collaboration has an info tooltip. | `audio-settings::collaboration::info` | `Manage microphone and audio settings for calls` | pass |
| Audio setting #2.c | Mic Noise Cancellation is a toggle. | `audio-settings::collaboration::component(mic-noise-cancellation)` | `toggle "Mic Noise Cancellation"` | pass |
| Audio setting #2.d | Mic Noise Cancellation has an info tooltip. | `audio-settings::collaboration::component(mic-noise-cancellation).info` | `Reduces background noise during calls` | pass |
| Audio setting #2.e | Sidetone is a toggle. | `audio-settings::collaboration::component(sidetone)` | `toggle "Sidetone"` | pass |
| Audio setting #2.f | Sidetone has an info tooltip. | `audio-settings::collaboration::component(sidetone).info` | `Hear your own voice through the headset` | pass |
| Audio setting #2.g | Sidetone owns the Sidetone Level dependent. | `audio-settings::collaboration::component(sidetone).dependents` | `slider "Sidetone Level"` | pass |
| Audio setting #2.h | Sidetone Level starts at 1. | `audio-settings::collaboration::component(sidetone).dependents.component(sidetone-level).min` | `1` | pass |
| Audio setting #2.i | Sidetone Level ends at 3. | `audio-settings::collaboration::component(sidetone).dependents.component(sidetone-level).max` | `3` | pass |
| Audio setting #3.a | Multimedia function exists. | `audio-settings::multimedia` | `function "Multimedia"` | pass |
| Audio setting #3.b | Multimedia presets are Bass Boost, Speech Boost, and Custom. | `audio-settings::multimedia::component(presets).options` | `bass-boost, speech-boost, custom` | pass |
| Audio setting #3.c | Bass Boost is selected by default. | `audio-settings::multimedia::component(presets).option(bass-boost).selected` | `true` | pass |
| Audio setting #3.d | Custom reveals EQ. | `audio-settings::multimedia::component(presets).reveals.custom` | `function "eq-audio"` | pass |
| Automated actions #1.a | Wear Detection function exists. | `automated-actions::wear-detection` | `function "Wear Detection"` | pass |
| Automated actions #1.b | Wear Detection has an info tooltip. | `automated-actions::wear-detection::info` | `Automatically detect when you're wearing the headset` | pass |
| Automated actions #1.c | Wear Detection is a parent toggle. | `automated-actions::wear-detection::component(toggle)` | `toggle` | pass |
| Automated actions #1.d | Wear Detection owns Sensor Sensitivity. | `automated-actions::wear-detection::dependents` | `segmented "Sensor Sensitivity"` | pass |
| Automated actions #1.e | Sensor Sensitivity options are Low and Normal. | `automated-actions::wear-detection::dependents.component(sensor-sensitivity).options` | `low, normal` | pass |
| Automated actions #1.f | Wear Detection owns When Headset Removed. | `automated-actions::wear-detection::dependents` | `card "When Headset Removed"` | pass |
| Automated actions #1.g | When Headset Removed includes Pause Music. | `automated-actions::wear-detection::dependents.card(when-headset-removed)::component(pause-music)` | `toggle "Pause Music"` | pass |
| Automated actions #1.h | Pause Music has an info tooltip. | `automated-actions::wear-detection::dependents.card(when-headset-removed)::component(pause-music).info` | `Pause audio when headset is removed` | pass |
| Automated actions #1.i | When Headset Removed includes Mute Microphone. | `automated-actions::wear-detection::dependents.card(when-headset-removed)::component(mute-microphone)` | `toggle "Mute Microphone"` | pass |
| Automated actions #1.j | Mute Microphone has an info tooltip. | `automated-actions::wear-detection::dependents.card(when-headset-removed)::component(mute-microphone).info` | `Mute microphone when headset is removed` | pass |
| Device settings #1.a | Auto Off function exists. | `device-settings::auto-off` | `function "Auto Off"` | pass |
| Device settings #1.b | Auto Off has an info tooltip. | `device-settings::auto-off::info` | `Automatically power off the headset after inactivity` | pass |
| Device settings #1.c | Auto Off is a toggle. | `device-settings::auto-off::component(toggle)` | `toggle` | pass |
| Device settings #1.d | Auto Off owns the Power off after dropdown. | `device-settings::auto-off::dependents` | `dropdown "Power off after"` | pass |
| Device settings #1.e | Power off after has the required inactive-time options. | `device-settings::auto-off::dependents.component(power-off-after).options` | `15m, 30m, 1h, 2h, 3h, 4h, 5h` | pass |
| Device settings #2.a | Audio Guidance function exists. | `device-settings::audio-guidance` | `function "Audio Guidance"` | pass |
| Device settings #2.b | Audio Guidance has an info tooltip. | `device-settings::audio-guidance::info` | `Get audio feedback for headset status and changes` | pass |
| Device settings #2.c | Audio Guidance is a toggle. | `device-settings::audio-guidance::component(toggle)` | `toggle` | pass |
| Device settings #2.d | Audio Guidance owns the Guidance Type control. | `device-settings::audio-guidance::dependents` | `segmented "Guidance Type"` | pass |
| Device settings #2.e | Guidance Type options are Tones and Voice. | `device-settings::audio-guidance::dependents.component(guidance-type).options` | `tones, voice` | pass |
| Device settings #3.a | Busy Light function exists. | `device-settings::busy-light` | `function "Busy Light"` | pass |
| Device settings #3.b | Busy Light has an info tooltip. | `device-settings::busy-light::info` | `Show a light indicator when you're on a call` | pass |
| Device settings #3.c | Busy Light is a toggle. | `device-settings::busy-light::component(toggle)` | `toggle` | pass |
| Device settings #4.a | Download Dell Audio uses the promotion-download function. | `device-settings::promotion-download` | `function "Download Dell Audio"` | pass |
