import Live
from Live.Clip import MidiNoteSpecification

class LiveAPIHandler:
    def __init__(self, control_surface):
        self.cs = control_surface

    def handle(self, method, params):
        self.cs.log_message(f"🔥 RECEIVED: {method} | params: {params}")
        handlers = {
            # ── Transport ──────────────────────────────────────────────────────
            "get_tempo":             self._get_tempo,
            "set_tempo":             self._set_tempo,
            "get_transport":         self._get_transport,
            "start_playing":         self._start_playing,
            "stop_playing":          self._stop_playing,
            "start_recording":       self._start_recording,
            "undo":                  self._undo,
            "redo":                  self._redo,
            # ── Session info ───────────────────────────────────────────────────
            "get_session_info":      self._get_session_info,
            "get_track_info":        self._get_track_info,
            # ── Track management ───────────────────────────────────────────────
            "create_midi_track":     self._create_midi_track,
            "create_audio_track":    self._create_audio_track,
            "delete_track":          self._delete_track,
            "set_track_name":        self._set_track_name,
            "set_track_volume":      self._set_track_volume,
            "set_track_pan":         self._set_track_pan,
            "set_track_mute":        self._set_track_mute,
            "set_track_solo":        self._set_track_solo,
            "set_track_arm":         self._set_track_arm,
            "set_track_routing":     self._set_track_routing,
            # ── Clip management ────────────────────────────────────────────────
            "create_clip":           self._create_clip,
            "delete_clip":           self._delete_clip,
            "set_clip_name":         self._set_clip_name,
            "duplicate_clip":        self._duplicate_clip,
            "set_clip_loop":         self._set_clip_loop,
            "quantize_clip":         self._quantize_clip,
            "fire_clip":             self._fire_clip,
            "stop_clip":             self._stop_clip,
            # ── Notes ──────────────────────────────────────────────────────────
            "add_notes":             self._add_notes,
            "get_clip_notes":        self._get_clip_notes,
            "clear_clip_notes":      self._clear_clip_notes,
            # ── Scenes ─────────────────────────────────────────────────────────
            "fire_scene":            self._fire_scene,
            "create_scene":          self._create_scene,
            "duplicate_scene":       self._duplicate_scene,
            "set_scene_name":        self._set_scene_name,
            # ── Arrangement ───────────────────────────────────────────────────
            "get_arrangement_clips":       self._get_arrangement_clips,
            "get_arrangement_clip_notes":  self._get_arrangement_clip_notes,
            "create_arrangement_clip":     self._create_arrangement_clip,
            "add_arrangement_notes":       self._add_arrangement_notes,
            "clear_arrangement_clip_notes": self._clear_arrangement_clip_notes,
            "delete_arrangement_clip":     self._delete_arrangement_clip,
            "set_arrangement_loop":        self._set_arrangement_loop,
            # ── Devices ────────────────────────────────────────────────────────
            "load_device":           self._load_device,
            "load_device_by_uri":    self._load_device_by_uri,
            "browse_devices":        self._browse_devices,
            "get_track_devices":     self._get_track_devices,
            "get_device_parameters": self._get_device_parameters,
            "set_device_parameter":  self._set_device_parameter,
            # ── Samples ────────────────────────────────────────────────────────
            "search_samples":        self._search_samples,
            "load_sample":           self._load_sample,
            "load_sample_into_drum_pad": self._load_sample_into_drum_pad,
            # ── Diagnostics ────────────────────────────────────────────────────
            "inspect_object":        self._inspect_object,
        }

        if method in handlers:
            try:
                return handlers[method](params)
            except Exception as e:
                self.cs.log_message(f"❌ ERROR in {method}: {e}")
                raise
        else:
            self.cs.log_message(f"❌ UNKNOWN METHOD: {method}")
            raise ValueError(f"Unknown method: {method}")

    # ═══════════════════════════════════════════════════════════════════════════
    # TRANSPORT
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_tempo(self, _):
        return {"tempo": self.cs.song().tempo}

    def _set_tempo(self, p):
        self.cs.song().tempo = float(p["tempo"])
        return {"success": True}

    def _get_transport(self, _):
        song = self.cs.song()
        return {"is_playing": song.is_playing, "is_recording": song.record_mode}

    def _start_playing(self, _):
        self.cs.song().start_playing()
        return {"success": True}

    def _stop_playing(self, _):
        self.cs.song().stop_playing()
        return {"success": True}

    def _start_recording(self, _):
        self.cs.song().record_mode = True
        return {"success": True}

    def _undo(self, _):
        self.cs.song().undo()
        return {"success": True}

    def _redo(self, _):
        self.cs.song().redo()
        return {"success": True}

    # ═══════════════════════════════════════════════════════════════════════════
    # SESSION INFO
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_session_info(self, _):
        """
        Full session snapshot — tracks, clips, devices, scenes.
        The AI should call this before making decisions about the session.
        """
        song        = self.cs.song()
        tracks_info = []
        for i, track in enumerate(song.tracks):
            clips = []
            for j, slot in enumerate(track.clip_slots):
                if slot.has_clip:
                    clips.append({
                        "slot":   j,
                        "name":   slot.clip.name,
                        "length": slot.clip.length,
                    })
            devices = [{"id": di, "name": d.name} for di, d in enumerate(track.devices)]
            # Detect track type so AI knows where MIDI clips/notes can go
            is_midi  = bool(getattr(track, "has_midi_input", False))
            is_audio = bool(getattr(track, "has_audio_input", False))
            if is_midi:
                track_type = "midi"
            elif is_audio:
                track_type = "audio"
            else:
                track_type = "unknown"

            # arm/solo can throw on return and group tracks
            try:
                arm = track.arm
            except Exception:
                arm = False
            try:
                solo = track.solo
            except Exception:
                solo = False

            # Count arrangement clips so the AI knows if content is in arrangement view
            try:
                arr_clips = list(track.arrangement_clips)
                arrangement_clip_count = len(arr_clips)
            except Exception:
                arrangement_clip_count = 0

            tracks_info.append({
                "index":   i,
                "name":    track.name,
                "type":    track_type,
                "mute":    track.mute,
                "solo":    solo,
                "arm":     arm,
                "volume":  track.mixer_device.volume.value,
                "devices": devices,
                "clips":   clips,
                "arrangement_clips_count": arrangement_clip_count,
            })

        scenes_info = [
            {"index": i, "name": s.name} for i, s in enumerate(song.scenes)
        ]

        return {
            "tempo":          song.tempo,
            "is_playing":     song.is_playing,
            "is_recording":   song.record_mode,
            "track_count":    len(song.tracks),
            "scene_count":    len(song.scenes),
            "selected_track": song.view.selected_track.name,
            "tracks":         tracks_info,
            "scenes":         scenes_info,
        }

    def _get_track_info(self, p):
        """
        Detailed info for a single track including full device parameter
        lists with min/max ranges. Call this after loading a device to
        know exactly what parameters are available to tweak.
        """
        track_idx = int(p.get("track", 0))
        track     = self._get_track(track_idx)
        devices   = []
        for di, device in enumerate(track.devices):
            params = [
                {
                    "id":    pi,
                    "name":  param.name,
                    "value": param.value,
                    "min":   param.min,
                    "max":   param.max,
                }
                for pi, param in enumerate(device.parameters)
            ]
            devices.append({
                "id":         di,
                "name":       device.name,
                "class_name": device.class_name,
                "parameters": params,
            })

        clips = []
        for j, slot in enumerate(track.clip_slots):
            if slot.has_clip:
                clips.append({
                    "slot":   j,
                    "name":   slot.clip.name,
                    "length": slot.clip.length,
                })

        # Detect track type
        is_midi  = bool(getattr(track, "has_midi_input", False))
        is_audio = bool(getattr(track, "has_audio_input", False))
        if is_midi:
            track_type = "midi"
        elif is_audio:
            track_type = "audio"
        else:
            track_type = "unknown"

        # arm/solo can throw on return and group tracks
        try:
            arm = track.arm
        except Exception:
            arm = False
        try:
            solo = track.solo
        except Exception:
            solo = False

        # Arrangement clips with start/end times
        arrangement_clips = []
        try:
            for ai, aclip in enumerate(track.arrangement_clips):
                arrangement_clips.append({
                    "index":      ai,
                    "name":       aclip.name,
                    "start_time": aclip.start_time,
                    "end_time":   aclip.end_time,
                    "length":     aclip.length,
                })
        except Exception:
            pass

        return {
            "index":   track_idx,
            "name":    track.name,
            "type":    track_type,
            "mute":    track.mute,
            "solo":    solo,
            "arm":     arm,
            "volume":  track.mixer_device.volume.value,
            "devices": devices,
            "clips":   clips,
            "arrangement_clips": arrangement_clips,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # TRACK MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_track(self, track_idx):
        """Safe getter — clamps to last track if index is out of range."""
        song   = self.cs.song()
        tracks = song.tracks
        if track_idx < 0 or track_idx >= len(tracks):
            self.cs.log_message(f"⚠️ Track {track_idx} out of range → using last track")
            track_idx = len(tracks) - 1
        return tracks[track_idx]

    def _create_midi_track(self, p):
        song      = self.cs.song()
        index     = p.get("index", -1)
        song.create_midi_track(index)
        new_index = len(song.tracks) - 1
        name      = p.get("name", "")
        if name:
            song.tracks[new_index].name = name
        self.cs.log_message(f"✅ Created MIDI track index={new_index} name='{name}'")
        return {"success": True, "track_index": new_index}

    def _create_audio_track(self, p):
        song      = self.cs.song()
        index     = p.get("index", -1)
        song.create_audio_track(index)
        new_index = len(song.tracks) - 1
        name      = p.get("name", "")
        if name:
            song.tracks[new_index].name = name
        self.cs.log_message(f"✅ Created audio track index={new_index} name='{name}'")
        return {"success": True, "track_index": new_index}

    def _delete_track(self, p):
        track_idx = int(p.get("track", 0))
        song      = self.cs.song()
        if track_idx < 0 or track_idx >= len(song.tracks):
            return {"success": False, "note": f"Track {track_idx} does not exist"}
        song.delete_track(track_idx)
        self.cs.log_message(f"✅ Deleted track {track_idx}")
        return {"success": True}

    def _set_track_name(self, p):
        track      = self._get_track(int(p.get("track", 0)))
        track.name = str(p["name"])
        self.cs.log_message(f"✅ Renamed track to '{track.name}'")
        return {"success": True}

    def _set_track_volume(self, p):
        self._get_track(int(p["track"])).mixer_device.volume.value = float(p.get("volume", 0.8))
        return {"success": True}

    def _set_track_pan(self, p):
        self._get_track(int(p["track"])).mixer_device.panning.value = float(p.get("pan", 0.0))
        return {"success": True}

    def _set_track_mute(self, p):
        self._get_track(int(p["track"])).mute = bool(p["mute"])
        return {"success": True}

    def _set_track_solo(self, p):
        self._get_track(int(p["track"])).solo = bool(p["solo"])
        return {"success": True}

    def _set_track_arm(self, p):
        self._get_track(int(p["track"])).arm = bool(p["arm"])
        return {"success": True}

    def _set_track_routing(self, p):
        track = self._get_track(int(p.get("track", 0)))
        if "input_type"  in p: track.input_routing_type  = p["input_type"]
        if "output_type" in p: track.output_routing_type = p["output_type"]
        return {"success": True}

    # ═══════════════════════════════════════════════════════════════════════════
    # CLIP MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def _create_clip(self, p):
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        length    = float(p.get("length", 4.0))
        track     = self._get_track(track_idx)

        # Guard: MIDI clips can only be created on MIDI tracks
        if not getattr(track, "has_midi_input", False):
            return {
                "success": False,
                "error":   "midi_track_required",
                "note":    f"Track {track_idx} is an audio track. MIDI clips can only "
                           f"be created on MIDI tracks. Use create_midi_track first, "
                           f"then target the new track.",
            }

        slot = track.clip_slots[clip_idx]
        if not slot.has_clip:
            slot.create_clip(length)
        name = p.get("name", "")
        if name and slot.has_clip:
            slot.clip.name = name
        self.cs.log_message(f"✅ Created clip track={track_idx} slot={clip_idx} length={length}")
        return {"success": True, "track": track_idx, "clip": clip_idx, "length": length}

    def _delete_clip(self, p):
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        slot      = self._get_track(track_idx).clip_slots[clip_idx]
        if slot.has_clip:
            slot.delete_clip()
            self.cs.log_message(f"✅ Deleted clip track={track_idx} slot={clip_idx}")
            return {"success": True}
        return {"success": False, "note": "No clip in that slot"}

    def _set_clip_name(self, p):
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        slot      = self._get_track(track_idx).clip_slots[clip_idx]
        if not slot.has_clip:
            return {"success": False, "note": "No clip in that slot"}
        slot.clip.name = str(p["name"])
        return {"success": True}

    def _duplicate_clip(self, p):
        """
        Copy a clip to another slot. dest_track defaults to same track,
        dest_clip defaults to src_clip + 1.
        """
        src_track_idx  = int(p.get("track", 0))
        src_clip_idx   = int(p.get("clip", 0))
        dest_track_idx = int(p.get("dest_track", src_track_idx))
        dest_clip_idx  = int(p.get("dest_clip", src_clip_idx + 1))

        src_slot  = self._get_track(src_track_idx).clip_slots[src_clip_idx]
        dest_slot = self._get_track(dest_track_idx).clip_slots[dest_clip_idx]

        if not src_slot.has_clip:
            return {"success": False, "note": "Source slot has no clip"}
        if dest_slot.has_clip:
            dest_slot.delete_clip()

        src_slot.duplicate_clip_to(dest_slot)
        self.cs.log_message(
            f"✅ Duplicated clip {src_track_idx}:{src_clip_idx} "
            f"→ {dest_track_idx}:{dest_clip_idx}"
        )
        return {"success": True, "dest_track": dest_track_idx, "dest_clip": dest_clip_idx}

    def _set_clip_loop(self, p):
        """Set loop start/end (in beats) and whether looping is on."""
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        slot      = self._get_track(track_idx).clip_slots[clip_idx]
        if not slot.has_clip:
            return {"success": False, "note": "No clip in that slot"}
        clip = slot.clip
        if "loop_start" in p: clip.loop_start = float(p["loop_start"])
        if "loop_end"   in p: clip.loop_end   = float(p["loop_end"])
        if "looping"    in p: clip.looping    = bool(p["looping"])
        return {"success": True}

    def _quantize_clip(self, p):
        """
        Quantize clip notes.
        quantize_to: 1=1/4, 2=1/8, 3=1/16, 4=1/32 (default 1/16)
        amount: 0.0–1.0 strength (default 1.0)
        """
        track_idx   = int(p.get("track", 0))
        clip_idx    = int(p.get("clip", 0))
        quantize_to = int(p.get("quantize_to", 3))
        amount      = float(p.get("amount", 1.0))
        slot        = self._get_track(track_idx).clip_slots[clip_idx]
        if not slot.has_clip:
            return {"success": False, "note": "No clip in that slot"}
        slot.clip.quantize(quantize_to, amount)
        self.cs.log_message(f"✅ Quantized clip track={track_idx} slot={clip_idx}")
        return {"success": True}

    def _fire_clip(self, p):
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        self._get_track(track_idx).clip_slots[clip_idx].fire()
        return {"success": True}

    def _stop_clip(self, p):
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        self._get_track(track_idx).clip_slots[clip_idx].stop()
        return {"success": True}

    # ═══════════════════════════════════════════════════════════════════════════
    # NOTES
    # ═══════════════════════════════════════════════════════════════════════════

    def _add_notes(self, p):
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        track     = self._get_track(track_idx)

        # Guard: notes can only be added to MIDI tracks
        if not getattr(track, "has_midi_input", False):
            return {
                "success": False,
                "error":   "midi_track_required",
                "note":    f"Track {track_idx} is an audio track. MIDI notes can only "
                           f"be added to MIDI tracks. Use create_midi_track first, "
                           f"then target the new track.",
            }

        slot = track.clip_slots[clip_idx]
        if not slot.has_clip:
            slot.create_clip(8.0)
        clip  = slot.clip
        notes = []
        for n in p["notes"]:
            start_time = n.get("start_time") or n.get("start", 0.0)
            notes.append(MidiNoteSpecification(
                pitch=int(n["pitch"]),
                start_time=float(start_time),
                duration=float(n.get("duration", 0.25)),
                velocity=int(n.get("velocity", 100)),
                mute=bool(n.get("mute", False))
            ))
        clip.add_new_notes(notes)
        self.cs.log_message(f"✅ Added {len(notes)} notes to track={track_idx} clip={clip_idx}")
        return {"success": True, "notes_added": len(notes), "track": track_idx, "clip": clip_idx}

    def _get_clip_notes(self, p):
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        slot      = self._get_track(track_idx).clip_slots[clip_idx]
        if not slot.has_clip:
            return {"notes": []}
        clip  = slot.clip
        notes = clip.get_notes_extended(0, 0, clip.length)
        return {"notes": [
            {
                "pitch":      n.pitch,
                "start_time": n.start_time,
                "duration":   n.duration,
                "velocity":   n.velocity,
                "mute":       n.mute,
            }
            for n in notes
        ]}

    def _clear_clip_notes(self, p):
        """Remove all notes from a clip without deleting the clip itself."""
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        slot      = self._get_track(track_idx).clip_slots[clip_idx]
        if not slot.has_clip:
            return {"success": False, "note": "No clip in that slot"}
        clip      = slot.clip
        all_notes = clip.get_notes_extended(0, 0, clip.length)
        clip.remove_notes_extended(0, 0, 128, clip.length)
        self.cs.log_message(
            f"✅ Cleared {len(all_notes)} notes from track={track_idx} clip={clip_idx}"
        )
        return {"success": True, "notes_cleared": len(all_notes)}

    # ═══════════════════════════════════════════════════════════════════════════
    # SCENES
    # ═══════════════════════════════════════════════════════════════════════════

    def _fire_scene(self, p):
        self.cs.song().scenes[int(p["scene"])].fire()
        return {"success": True}

    def _create_scene(self, p):
        song      = self.cs.song()
        index     = int(p.get("index", -1))
        song.create_scene(index)
        new_index = len(song.scenes) - 1
        name      = p.get("name", "")
        if name:
            song.scenes[new_index].name = name
        self.cs.log_message(f"✅ Created scene index={new_index} name='{name}'")
        return {"success": True, "scene_index": new_index}

    def _duplicate_scene(self, p):
        """Duplicate a scene — use this to build intro/verse/drop/outro sections."""
        song      = self.cs.song()
        scene_idx = int(p.get("scene", 0))
        if scene_idx < 0 or scene_idx >= len(song.scenes):
            return {"success": False, "note": f"Scene {scene_idx} does not exist"}
        song.duplicate_scene(scene_idx)
        new_index = scene_idx + 1
        self.cs.log_message(f"✅ Duplicated scene {scene_idx} → {new_index}")
        return {"success": True, "new_scene_index": new_index}

    def _set_scene_name(self, p):
        song      = self.cs.song()
        scene_idx = int(p.get("scene", 0))
        if scene_idx < 0 or scene_idx >= len(song.scenes):
            return {"success": False, "note": f"Scene {scene_idx} does not exist"}
        song.scenes[scene_idx].name = str(p["name"])
        return {"success": True}

    # ═══════════════════════════════════════════════════════════════════════════
    # DEVICES
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_track_devices(self, p):
        track = self._get_track(int(p.get("track", 0)))
        return {"devices": [
            {"id": i, "name": d.name, "class_name": d.class_name}
            for i, d in enumerate(track.devices)
        ]}

    def _get_device_parameters(self, p):
        """
        Returns all parameters with min/max ranges.
        Always call this after load_device before setting parameters.
        """
        track  = self._get_track(int(p.get("track", 0)))
        device = track.devices[int(p.get("device", 0))]
        return {
            "device_name": device.name,
            "parameters": [
                {
                    "id":    i,
                    "name":  param.name,
                    "value": param.value,
                    "min":   param.min,
                    "max":   param.max,
                }
                for i, param in enumerate(device.parameters)
            ]
        }

    def _set_device_parameter(self, p):
        """
        Set a device parameter by id. Value is automatically clamped to
        the valid min/max range so bad values won't throw an error.
        """
        track     = self._get_track(int(p.get("track", 0)))
        device    = track.devices[int(p.get("device", 0))]
        param_idx = int(p.get("parameter", 0))
        param     = device.parameters[param_idx]
        value     = float(p["value"])
        value     = max(param.min, min(param.max, value))
        param.value = value
        self.cs.log_message(
            f"✅ Set '{param.name}' on '{device.name}' → {value}"
        )
        return {"success": True, "parameter": param.name, "new_value": value}

    # ─── Browser helpers ──────────────────────────────────────────────────────

    def _score_item(self, item_name, search_name):
        i = item_name.lower()
        s = search_name.lower()
        for ext in (".adg", ".adv", ".als", ".asd"):
            i = i.replace(ext, "")
            s = s.replace(ext, "")
        i = i.strip()
        s = s.strip()
        if i == s:   return 3
        if s in i:   return 2
        words = s.split()
        if len(words) > 1 and all(w in i for w in words): return 1
        return 0

    def _search_browser_node(self, node, search_name, results,
                              depth=0, max_depth=8, path=""):
        if depth > max_depth:
            return
        try:
            children = node.iter_children
        except Exception:
            return
        for item in children:
            try:
                item_name = item.name or ""
                score     = self._score_item(item_name, search_name)
                item_path = f"{path}/{item_name}" if path else item_name
                if score > 0 and getattr(item, "is_loadable", False):
                    results.append((score, item_name, item, item_path))
                    self.cs.log_message(f"  🎯 score={score}: {item_path}")
                self._search_browser_node(item, search_name, results,
                                          depth + 1, max_depth, item_path)
            except Exception as e:
                self.cs.log_message(f"  ⚠️ scan error depth={depth}: {e}")

    def _find_best_browser_match(self, search_name):
        browser    = self.cs.application().browser
        categories = [
            ("drums",         browser.drums),
            ("instruments",   browser.instruments),
            ("audio_effects", browser.audio_effects),
            ("midi_effects",  browser.midi_effects),
            ("plugins",       browser.plugins),
            ("sounds",        browser.sounds),
            ("packs",         browser.packs),
        ]
        best_score = 0
        best_item  = None
        best_path  = ""
        for cat_name, category in categories:
            self.cs.log_message(f"🔎 Searching '{cat_name}' for '{search_name}'...")
            results = []
            self._search_browser_node(category, search_name, results, path=cat_name)
            if results:
                results.sort(key=lambda x: (-x[0], len(x[3])))
                top_score, top_name, top_item, top_path = results[0]
                self.cs.log_message(
                    f"  ✅ Best in '{cat_name}': '{top_name}' score={top_score}"
                )
                if top_score > best_score:
                    best_score = top_score
                    best_item  = top_item
                    best_path  = top_path
            else:
                self.cs.log_message(f"  — Nothing in '{cat_name}'")
        return best_item, best_score, best_path

    def _load_device(self, p):
        """
        Primary device loading. Searches all browser categories by name.
        Returns device parameters automatically after loading so the AI
        can tweak the sound without needing an extra round trip.
        """
        track_idx   = int(p.get("track", 0))
        device_name = str(p.get("device_name", "")).strip()
        song        = self.cs.song()

        self.cs.log_message(
            f"🔍 load_device: '{device_name}' → track {track_idx} "
            f"(total tracks: {len(song.tracks)})"
        )

        track = self._get_track(track_idx)
        song.view.selected_track = track

        item, score, path = self._find_best_browser_match(device_name)

        if item:
            self.cs.log_message(f"🎉 Loading '{item.name}' score={score} path={path}")
            try:
                self.cs.application().browser.load_item(item)
                self.cs.log_message(f"✅ Loaded '{item.name}' on track {track_idx}")

                # Return parameters immediately so AI can tweak without extra call
                params_info = []
                if track.devices:
                    last_device = track.devices[-1]
                    params_info = [
                        {
                            "id":    i,
                            "name":  param.name,
                            "value": param.value,
                            "min":   param.min,
                            "max":   param.max,
                        }
                        for i, param in enumerate(last_device.parameters)
                    ]

                return {
                    "success":     True,
                    "device":      item.name,
                    "message":     f"Loaded '{item.name}' on track {track_idx}",
                    "match_score": score,
                    "match_path":  path,
                    "device_id":   len(track.devices) - 1,
                    "parameters":  params_info,
                }
            except Exception as e:
                self.cs.log_message(f"❌ load_item failed: {e}")
                return {
                    "success": False,
                    "note":    f"Found '{item.name}' but load failed: {e}",
                    "message": f"Found '{item.name}' but load failed: {e}",
                }

        self.cs.log_message(f"❌ Could not find '{device_name}'")
        return {
            "success": False,
            "note":    f"Could not find '{device_name}' in Ableton's browser",
            "message": f"Could not find '{device_name}' in Ableton's browser",
        }

    def _load_device_by_uri(self, p):
        """URI-based loading with name fallback."""
        track_idx = int(p.get("track", 0))
        uri       = str(p.get("uri", "")).strip()

        self.cs.log_message(f"🔍 load_device_by_uri: '{uri}' → track {track_idx}")

        track   = self._get_track(track_idx)
        song    = self.cs.song()
        song.view.selected_track = track
        browser = self.cs.application().browser

        item = self._find_item_by_uri(browser, uri)
        if item:
            self.cs.log_message(f"✅ URI match: '{item.name}'")
            try:
                browser.load_item(item)
                return {
                    "success": True,
                    "device":  item.name,
                    "message": f"Loaded '{item.name}' via URI on track {track_idx}",
                }
            except Exception as e:
                self.cs.log_message(f"❌ URI load failed: {e}")

        uri_leaf   = uri.split("/")[-1] if "/" in uri else uri
        name_guess = uri_leaf.replace(".adg", "").replace(".adv", "").strip()
        self.cs.log_message(f"⚠️ No URI match — trying name: '{name_guess}'")

        item, score, path = self._find_best_browser_match(name_guess)
        if item:
            try:
                browser.load_item(item)
                return {
                    "success":     True,
                    "device":      item.name,
                    "message":     f"Loaded '{item.name}' (name fallback) on track {track_idx}",
                    "match_score": score,
                    "match_path":  path,
                }
            except Exception as e:
                return {
                    "success": False,
                    "note":    f"Found '{item.name}' but load failed: {e}",
                    "message": f"Found '{item.name}' but load failed: {e}",
                }

        return {
            "success": False,
            "note":    f"Could not resolve URI or name for '{uri}'",
            "message": f"Could not resolve URI or name for '{uri}'",
        }

    def _find_item_by_uri(self, browser, uri):
        for category in [browser.drums, browser.instruments,
                         browser.audio_effects, browser.midi_effects,
                         browser.plugins, browser.sounds, browser.packs]:
            result = self._walk_for_uri(category, uri)
            if result:
                return result
        return None

    def _walk_for_uri(self, node, uri, depth=0, max_depth=8):
        if depth > max_depth:
            return None
        try:
            for item in node.iter_children:
                try:
                    item_uri = getattr(item, "uri", None)
                    if item_uri and str(item_uri) == uri and getattr(item, "is_loadable", False):
                        return item
                    result = self._walk_for_uri(item, uri, depth + 1, max_depth)
                    if result:
                        return result
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _browse_devices(self, p):
        """
        Diagnostic tool — list browser contents.
        Params: category, search (optional filter), max_depth
        """
        cat_name  = p.get("category", "drums")
        search    = p.get("search", "").strip().lower()
        max_depth = min(int(p.get("max_depth", 4)), 8)
        browser   = self.cs.application().browser
        cat_map   = {
            "drums":         browser.drums,
            "instruments":   browser.instruments,
            "audio_effects": browser.audio_effects,
            "midi_effects":  browser.midi_effects,
            "plugins":       browser.plugins,
            "sounds":        browser.sounds,
            "packs":         browser.packs,
        }
        category = cat_map.get(cat_name)
        if category is None:
            return {"error": f"Unknown category '{cat_name}'. Use: {list(cat_map.keys())}"}
        items_found = []
        self._collect_items(category, items_found, search, max_depth, path=cat_name)
        self.cs.log_message(
            f"browse_devices '{cat_name}' search='{search}' → {len(items_found)} items"
        )
        return {
            "category": cat_name,
            "search":   search or "(all)",
            "count":    len(items_found),
            "items":    items_found[:100],
        }

    def _collect_items(self, node, out, search, max_depth, depth=0, path=""):
        if depth > max_depth:
            return
        try:
            for item in node.iter_children:
                try:
                    name      = item.name or ""
                    item_path = f"{path}/{name}" if path else name
                    loadable  = getattr(item, "is_loadable", False)
                    uri       = str(getattr(item, "uri", ""))
                    if not search or search in name.lower():
                        out.append({
                            "name":     name,
                            "path":     item_path,
                            "loadable": loadable,
                            "uri":      uri,
                            "depth":    depth,
                        })
                    self._collect_items(item, out, search, max_depth, depth + 1, item_path)
                except Exception:
                    continue
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════════
    # SAMPLES
    # ═══════════════════════════════════════════════════════════════════════════

    def _search_samples(self, p):
        """
        Search Ableton's sample library for files matching a query.
        Params: query (required), max_results (optional, default 20)
        Returns list of {name, path, uri} that can be loaded via load_sample.
        """
        query       = (p.get("query") or "").strip().lower()
        max_results = min(int(p.get("max_results", 20)), 100)
        if not query:
            return {"error": "query is required"}

        browser = self.cs.application().browser
        results = []

        # Samples live in browser.samples AND inside many pack folders,
        # so scan both for maximum coverage.
        for root_name, root in [("samples", browser.samples), ("packs", browser.packs)]:
            self._collect_samples(root, query, results, max_depth=10, path=root_name)
            if len(results) >= max_results:
                break

        # Sort so exact name matches come first, then shorter names
        def score(item):
            name_lower = item["name"].lower()
            if name_lower == query:           return (0, len(name_lower))
            if name_lower.startswith(query):  return (1, len(name_lower))
            if query in name_lower:           return (2, len(name_lower))
            return (3, len(name_lower))
        results.sort(key=score)

        self.cs.log_message(f"🔎 search_samples '{query}' → {len(results)} matches")
        return {
            "query":   query,
            "count":   len(results),
            "samples": results[:max_results],
        }

    def _collect_samples(self, node, query, out, max_depth, depth=0, path=""):
        if depth > max_depth:
            return
        try:
            for item in node.iter_children:
                try:
                    name      = item.name or ""
                    item_path = f"{path}/{name}" if path else name
                    is_sample = name.lower().endswith(
                        (".wav", ".aif", ".aiff", ".flac", ".mp3", ".ogg", ".m4a")
                    )
                    if is_sample and query in name.lower():
                        uri = str(getattr(item, "uri", ""))
                        out.append({"name": name, "path": item_path, "uri": uri})
                    # Always recurse — sample folders can nest deeply inside packs
                    self._collect_samples(item, query, out, max_depth, depth + 1, item_path)
                except Exception:
                    continue
        except Exception:
            pass

    def _load_sample(self, p):
        """
        Load a sample into the session. Two modes:
          - mode='simpler'    → Drop onto MIDI track wrapped in Simpler (playable).
          - mode='audio_clip' → Drop as an audio clip in a clip slot on an audio track.
          - mode='auto' (default) → Pick based on the target track's type.

        Params:
          track       (required) — track index to target
          sample_name OR uri     — one is required
          mode                   — 'auto' | 'simpler' | 'audio_clip' (default 'auto')
          clip        (optional) — for audio_clip mode, which clip slot (default 0)
          auto_create (optional) — if True and track type doesn't match mode,
                                   create a new track of the correct type (default True)
        """
        track_idx   = int(p["track"])
        sample_name = (p.get("sample_name") or "").strip()
        uri         = (p.get("uri") or "").strip()
        mode        = (p.get("mode") or "auto").strip().lower()
        clip_idx    = int(p.get("clip", 0))
        auto_create = bool(p.get("auto_create", True))

        if not sample_name and not uri:
            return {"error": "Provide sample_name or uri"}
        if mode not in ("auto", "simpler", "audio_clip"):
            return {"error": "mode must be 'auto', 'simpler', or 'audio_clip'"}

        song    = self.cs.song()
        browser = self.cs.application().browser

        if track_idx < 0 or track_idx >= len(song.tracks):
            return {"error": f"Track {track_idx} does not exist"}

        # ── Detect track type and reconcile with requested mode ───────────────
        target_track = song.tracks[track_idx]
        is_midi      = bool(getattr(target_track, "has_midi_input", False))
        is_audio     = bool(getattr(target_track, "has_audio_input", False))

        if mode == "auto":
            mode = "simpler" if is_midi else "audio_clip"
            self.cs.log_message(f"🔍 Auto mode → '{mode}' (track {track_idx} is {'MIDI' if is_midi else 'audio'})")

        # Handle mismatch: MIDI track but user wants audio_clip (or vice versa)
        mismatched = (mode == "simpler" and not is_midi) or (mode == "audio_clip" and not is_audio)
        if mismatched:
            if not auto_create:
                return {
                    "success": False,
                    "message": f"Track {track_idx} is not the right type for mode '{mode}'. "
                               f"Set auto_create=True or pick a different track.",
                }
            # Create a new track of the correct type at the end
            if mode == "simpler":
                song.create_midi_track(-1)
                self.cs.log_message(f"✅ Auto-created MIDI track for Simpler load")
            else:
                song.create_audio_track(-1)
                self.cs.log_message(f"✅ Auto-created audio track for audio clip load")
            track_idx    = len(song.tracks) - 1
            target_track = song.tracks[track_idx]

        # ── Find the sample in the browser ───────────────────────────────────
        item = None
        if uri:
            for root in (browser.samples, browser.packs):
                item = self._walk_for_uri(root, uri)
                if item:
                    break
        if item is None and sample_name:
            search_result = self._search_samples({"query": sample_name, "max_results": 1})
            if search_result.get("count", 0) > 0:
                target_uri = search_result["samples"][0]["uri"]
                for root in (browser.samples, browser.packs):
                    item = self._walk_for_uri(root, target_uri)
                    if item:
                        break
        if item is None:
            return {
                "success": False,
                "message": f"Could not find sample matching '{sample_name or uri}'",
            }

        # ── Load based on mode ───────────────────────────────────────────────
        try:
            if mode == "simpler":
                # Select the MIDI track; Live wraps the sample in Simpler automatically
                song.view.selected_track = target_track
                browser.load_item(item)
                self.cs.log_message(f"✅ Loaded '{item.name}' into Simpler on track {track_idx}")
                return {
                    "success": True,
                    "sample":  item.name,
                    "track":   track_idx,
                    "mode":    "simpler",
                    "message": f"Loaded '{item.name}' into Simpler on track {track_idx}",
                }
            else:
                # audio_clip mode: select the clip slot so Live drops the sample there as a clip
                if clip_idx < 0 or clip_idx >= len(target_track.clip_slots):
                    return {"error": f"Clip slot {clip_idx} does not exist on track {track_idx}"}
                song.view.selected_track = target_track
                target_track.view.select_instrument  # no-op on audio, but safe
                song.view.highlighted_clip_slot = target_track.clip_slots[clip_idx]
                browser.load_item(item)
                self.cs.log_message(f"✅ Loaded '{item.name}' as audio clip on track {track_idx} slot {clip_idx}")
                return {
                    "success": True,
                    "sample":  item.name,
                    "track":   track_idx,
                    "clip":    clip_idx,
                    "mode":    "audio_clip",
                    "message": f"Loaded '{item.name}' as audio clip on track {track_idx}, slot {clip_idx}",
                }
        except Exception as e:
            return {"success": False, "message": f"Failed to load: {e}"}

    def _load_sample_into_drum_pad(self, p):
        """
        Load a sample into a specific pad in a Drum Rack.
        Params: track, device (the Drum Rack's index), pad (MIDI note number 0-127),
                sample_name OR uri
        """
        track_idx  = int(p["track"])
        device_idx = int(p.get("device", 0))
        pad_note   = int(p["pad"])

        song  = self.cs.song()
        track = song.tracks[track_idx]
        if device_idx >= len(track.devices):
            return {"error": f"No device at index {device_idx} on track {track_idx}"}

        drum_rack = track.devices[device_idx]
        if not getattr(drum_rack, "can_have_drum_pads", False):
            return {"error": f"Device '{drum_rack.name}' is not a Drum Rack"}

        # Select the target pad so the browser loads into it
        try:
            drum_rack.view.selected_drum_pad = drum_rack.drum_pads[pad_note]
        except Exception as e:
            return {"error": f"Could not select pad {pad_note}: {e}"}

        # Reuse the sample-loading logic
        result = self._load_sample({
            "track":       track_idx,
            "sample_name": p.get("sample_name", ""),
            "uri":         p.get("uri", ""),
        })
        if result.get("success"):
            result["pad"] = pad_note
            result["message"] = f"Loaded '{result['sample']}' into pad {pad_note} on Drum Rack"
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # ARRANGEMENT VIEW
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_arrangement_clip(self, track_idx, clip_idx):
        """Safe getter for an arrangement clip by track and clip index."""
        track = self._get_track(track_idx)
        try:
            arr_clips = list(track.arrangement_clips)
        except Exception:
            return None, "Track has no arrangement_clips property"
        if clip_idx < 0 or clip_idx >= len(arr_clips):
            return None, f"Arrangement clip {clip_idx} does not exist on track {track_idx} (has {len(arr_clips)} clips)"
        return arr_clips[clip_idx], None

    def _get_arrangement_clips(self, p):
        """
        List all clips in arrangement view for a track.
        Returns clip index, name, start/end time, and length.
        The AI should call this to discover what content exists in arrangement view.
        """
        track_idx = int(p.get("track", 0))
        track     = self._get_track(track_idx)
        clips     = []
        try:
            for i, clip in enumerate(track.arrangement_clips):
                clips.append({
                    "index":      i,
                    "name":       clip.name,
                    "start_time": clip.start_time,
                    "end_time":   clip.end_time,
                    "length":     clip.length,
                })
        except Exception as e:
            return {"success": False, "error": f"Cannot read arrangement clips: {e}"}

        self.cs.log_message(
            f"✅ get_arrangement_clips track={track_idx} → {len(clips)} clips"
        )
        return {
            "success": True,
            "track":   track_idx,
            "count":   len(clips),
            "clips":   clips,
        }

    def _get_arrangement_clip_notes(self, p):
        """
        Read MIDI notes from an arrangement clip.
        Params: track, clip (arrangement clip index)
        Works the same as get_clip_notes but for arrangement view.
        """
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))

        clip, err = self._get_arrangement_clip(track_idx, clip_idx)
        if err:
            return {"success": False, "note": err}

        try:
            notes = clip.get_notes_extended(0, 0, clip.length)
        except Exception:
            # Some Live versions use different signature
            try:
                notes = clip.get_notes_extended(0, 0, 128, clip.length)
            except Exception as e:
                return {"success": False, "error": f"Cannot read notes: {e}"}

        result_notes = [
            {
                "pitch":      n.pitch,
                "start_time": n.start_time,
                "duration":   n.duration,
                "velocity":   n.velocity,
                "mute":       n.mute,
            }
            for n in notes
        ]
        self.cs.log_message(
            f"✅ get_arrangement_clip_notes track={track_idx} clip={clip_idx} → {len(result_notes)} notes"
        )
        return {
            "success":   True,
            "track":     track_idx,
            "clip":      clip_idx,
            "clip_name": clip.name,
            "length":    clip.length,
            "notes":     result_notes,
        }

    def _create_arrangement_clip(self, p):
        """
        Create a new MIDI clip in arrangement view at a specific beat position.
        Params: track, start_time (in beats), length (in beats)
        Note: Only works on MIDI tracks in Live 11+.
        """
        track_idx  = int(p.get("track", 0))
        start_time = float(p.get("start_time", 0.0))
        length     = float(p.get("length", 4.0))
        track      = self._get_track(track_idx)

        # Guard: MIDI clips can only be created on MIDI tracks
        if not getattr(track, "has_midi_input", False):
            return {
                "success": False,
                "error":   "midi_track_required",
                "note":    f"Track {track_idx} is an audio track. Arrangement MIDI clips "
                           f"can only be created on MIDI tracks.",
            }

        try:
            clip = track.create_arrangement_clip(start_time, length)
            name = p.get("name", "")
            if name:
                clip.name = name

            self.cs.log_message(
                f"✅ Created arrangement clip track={track_idx} "
                f"start={start_time} length={length}"
            )

            # Find the index of the new clip
            clip_idx = 0
            try:
                for i, c in enumerate(track.arrangement_clips):
                    if c == clip:
                        clip_idx = i
                        break
            except Exception:
                pass

            return {
                "success":    True,
                "track":      track_idx,
                "clip":       clip_idx,
                "start_time": start_time,
                "length":     length,
            }
        except AttributeError:
            return {
                "success": False,
                "error":   "not_supported",
                "note":    "create_arrangement_clip is not available in this version of "
                           "Ableton Live. Try creating clips in session view instead.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_arrangement_notes(self, p):
        """
        Add MIDI notes to an existing arrangement clip.
        Params: track, clip (arrangement clip index), notes (same format as add_notes)
        """
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))

        clip, err = self._get_arrangement_clip(track_idx, clip_idx)
        if err:
            return {"success": False, "note": err}

        notes = []
        for n in p["notes"]:
            start_time = n.get("start_time") or n.get("start", 0.0)
            notes.append(MidiNoteSpecification(
                pitch=int(n["pitch"]),
                start_time=float(start_time),
                duration=float(n.get("duration", 0.25)),
                velocity=int(n.get("velocity", 100)),
                mute=bool(n.get("mute", False))
            ))
        clip.add_new_notes(notes)
        self.cs.log_message(
            f"✅ Added {len(notes)} notes to arrangement clip "
            f"track={track_idx} clip={clip_idx}"
        )
        return {
            "success":     True,
            "notes_added": len(notes),
            "track":       track_idx,
            "clip":        clip_idx,
        }

    def _clear_arrangement_clip_notes(self, p):
        """Remove all notes from an arrangement clip without deleting it."""
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))

        clip, err = self._get_arrangement_clip(track_idx, clip_idx)
        if err:
            return {"success": False, "note": err}

        try:
            all_notes = clip.get_notes_extended(0, 0, clip.length)
            clip.remove_notes_extended(0, 0, 128, clip.length)
        except Exception:
            try:
                all_notes = clip.get_notes_extended(0, 0, 128, clip.length)
                clip.remove_notes_extended(0, 0, 128, clip.length)
            except Exception as e:
                return {"success": False, "error": f"Cannot clear notes: {e}"}

        self.cs.log_message(
            f"✅ Cleared {len(all_notes)} notes from arrangement clip "
            f"track={track_idx} clip={clip_idx}"
        )
        return {"success": True, "notes_cleared": len(all_notes)}

    def _delete_arrangement_clip(self, p):
        """
        Delete an arrangement clip by index.
        Params: track, clip (arrangement clip index)
        """
        track_idx = int(p.get("track", 0))
        clip_idx  = int(p.get("clip", 0))
        track     = self._get_track(track_idx)

        try:
            arr_clips = list(track.arrangement_clips)
        except Exception:
            return {"success": False, "error": "Cannot access arrangement clips"}

        if clip_idx < 0 or clip_idx >= len(arr_clips):
            return {"success": False, "note": f"Arrangement clip {clip_idx} does not exist"}

        try:
            clip = arr_clips[clip_idx]
            clip.remove()
            self.cs.log_message(
                f"✅ Deleted arrangement clip {clip_idx} from track {track_idx}"
            )
            return {"success": True}
        except AttributeError:
            # Try alternative removal method
            try:
                track.delete_clip(clip)
                self.cs.log_message(
                    f"✅ Deleted arrangement clip {clip_idx} from track {track_idx}"
                )
                return {"success": True}
            except Exception as e2:
                return {
                    "success": False,
                    "error":   "not_supported",
                    "note":    f"Cannot delete arrangement clips in this version: {e2}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _set_arrangement_loop(self, p):
        """
        Set the arrangement loop brace position and toggle.
        Params: start (in beats), length (in beats), enabled (bool, optional)
        """
        song = self.cs.song()
        if "start" in p:
            song.loop_start = float(p["start"])
        if "length" in p:
            song.loop_length = float(p["length"])
        if "enabled" in p:
            song.loop = bool(p["enabled"])
        self.cs.log_message(
            f"✅ Set arrangement loop: start={song.loop_start} "
            f"length={song.loop_length} enabled={song.loop}"
        )
        return {
            "success":     True,
            "loop_start":  song.loop_start,
            "loop_length": song.loop_length,
            "loop_enabled": song.loop,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # DIAGNOSTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def _inspect_object(self, p):
        try:
            obj  = self.cs.song()
            path = p.get("path", "song")
            for part in path.replace("song.", "").split("."):
                if "[" in part:
                    name, idx = part.split("[")
                    obj = getattr(obj, name)[int(idx.rstrip("]"))]
                else:
                    obj = getattr(obj, part)
            return {
                "type": type(obj).__name__,
                "dir":  [x for x in dir(obj) if not x.startswith("_")],
            }
        except Exception as e:
            return {"error": str(e)}
