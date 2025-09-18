# dj_mix_config.py
"""
DJ MIX Configuration for OpenMoxie
Defines combined audio + dance behavior commands for the DJ MIX panel
"""

# DJ MIX Commands - Combined Audio + Dance Behavior pairs
DJ_MIX_COMMANDS = {
    # Zaygo Dance Series (140 BPM)
    'zaygo_long_140': {
        'name': 'Zaygo Long Dance (140 BPM)',
        'description': 'Extended Zaygo dance routine with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-zaygolong140bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:60.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_zaygo_long_140bpm+,+Track+:++}"/>',
        'category': 'zaygo',
        'bpm': 140,
        'duration': 60
    },
    'zaygo_medium_140': {
        'name': 'Zaygo Medium Dance (140 BPM)',
        'description': 'Medium-length Zaygo dance with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-zaygomedium140bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:30.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_zaygo_medium_140bpm+,+Track+:++}"/>',
        'category': 'zaygo',
        'bpm': 140,
        'duration': 30
    },
    'zaygo_short_140': {
        'name': 'Zaygo Short Dance (140 BPM)',
        'description': 'Quick Zaygo dance burst with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-zaygoshort140bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:15.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_zaygo_short_140bpm+,+Track+:++}"/>',
        'category': 'zaygo',
        'bpm': 140,
        'duration': 15
    },

    # Karu Dance Series (135 BPM)
    'karu_long_135': {
        'name': 'Karu Long Dance (135 BPM)',
        'description': 'Extended Karu dance routine with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-karulong135bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:60.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_karu_long_135bpm+,+Track+:++}"/>',
        'category': 'karu',
        'bpm': 135,
        'duration': 60
    },
    'karu_medium_135': {
        'name': 'Karu Medium Dance (135 BPM)',
        'description': 'Medium-length Karu dance with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-karumedium135bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:30.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_karu_medium_135bpm+,+Track+:++}"/>',
        'category': 'karu',
        'bpm': 135,
        'duration': 30
    },
    'karu_short_135': {
        'name': 'Karu Short Dance (135 BPM)',
        'description': 'Quick Karu dance burst with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-karushort135bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:15.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_karu_short_135bpm+,+Track+:++}"/>',
        'category': 'karu',
        'bpm': 135,
        'duration': 15
    },

    # Farfel Dance Series (130 BPM)
    'farfel_long_130': {
        'name': 'Farfel Long Dance (130 BPM)',
        'description': 'Extended Farfel dance routine with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-farfellong130bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:60.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_farfel_long_130bpm+,+Track+:++}"/>',
        'category': 'farfel',
        'bpm': 130,
        'duration': 60
    },
    'farfel_medium_130': {
        'name': 'Farfel Medium Dance (130 BPM)',
        'description': 'Medium-length Farfel dance with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-farfelmedium130bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:30.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_farfel_medium_130bpm+,+Track+:++}"/>',
        'category': 'farfel',
        'bpm': 130,
        'duration': 30
    },
    'farfel_short_130': {
        'name': 'Farfel Short Dance (130 BPM)',
        'description': 'Quick Farfel dance burst with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-farfelshort130bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:15.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_farfel_short_130bpm+,+Track+:++}"/>',
        'category': 'farfel',
        'bpm': 130,
        'duration': 15
    },

    # Cruncher Dance Series (120 BPM)
    'cruncher_long_120': {
        'name': 'Cruncher Long Dance (120 BPM)',
        'description': 'Extended Cruncher dance routine with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-cruncherlong120bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:60.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_cruncher_long_120bpm+,+Track+:++}"/>',
        'category': 'cruncher',
        'bpm': 120,
        'duration': 60
    },
    'cruncher_medium_120': {
        'name': 'Cruncher Medium Dance (120 BPM)',
        'description': 'Medium-length Cruncher dance with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-crunchermedium120bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:30.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_cruncher_medium_120bpm+,+Track+:++}"/>',
        'category': 'cruncher',
        'bpm': 120,
        'duration': 30
    },
    'cruncher_short_120': {
        'name': 'Cruncher Short Dance (120 BPM)',
        'description': 'Quick Cruncher dance burst with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemoves-crunchershort120bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:15.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_cruncher_short_120bpm+,+Track+:++}"/>',
        'category': 'cruncher',
        'bpm': 120,
        'duration': 15
    },

    # Professor Dance Series (120 BPM)
    'professor_long_120': {
        'name': 'Professor Long Dance (120 BPM)',
        'description': 'Extended Professor dance routine with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedancemovesprofessorlong4-4120bpm+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:60.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_professor_long_120bpm+,+Track+:++}"/>',
        'category': 'professor',
        'bpm': 120,
        'duration': 60
    },

    # Special Dance Combinations
    'happy_birthday_dance': {
        'name': 'Happy Birthday Dance',
        'description': 'Special birthday celebration dance with music',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+moxiedances-happybirthdayfullv1+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:45.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_happy_birthday_long_120bpm+,+Track+:++}"/>',
        'category': 'special',
        'bpm': 120,
        'duration': 45
    },

    'freeze_dance': {
        'name': 'Freeze Dance',
        'description': 'Interactive freeze dance game',
        'audio_command': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+sfx_moxie_dance_moves+,+LoopSound+:true,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:1.0,+AudioTimelineField+:+none+}"/>',
        'behavior_command': '<mark name="cmd:behaviour-tree,data:{+transition+:0.5,+duration+:30.0,+repeat+:1,+layerBlendInTime+:0.5,+layerBlendOutTime+:0.5,+blocking+:false,+action+:0,+variableName+:++,+variableValue+:++,+eventName+:+Gesture_None+,+lifetime+:0,+category+:+None+,+behaviour+:+bht_dance_freezedance+,+Track+:++}"/>',
        'category': 'special',
        'bpm': 120,
        'duration': 30
    }
}

# Category-based organization for the UI
DJ_MIX_CATEGORIES = {
    'zaygo': {
        'name': 'Zaygo Dances',
        'description': 'High-energy 140 BPM dances featuring Zaygo character',
        'color': '#ff6b6b',
        'icon': '🎵'
    },
    'karu': {
        'name': 'Karu Dances',
        'description': 'Moderate 135 BPM dances featuring Karu character',
        'color': '#4ecdc4',
        'icon': '🎶'
    },
    'farfel': {
        'name': 'Farfel Dances',
        'description': 'Chill 130 BPM dances featuring Farfel character',
        'color': '#45b7d1',
        'icon': '🎼'
    },
    'cruncher': {
        'name': 'Cruncher Dances',
        'description': 'Groovy 120 BPM dances featuring Cruncher character',
        'color': '#96ceb4',
        'icon': '🎤'
    },
    'professor': {
        'name': 'Professor Dances',
        'description': 'Educational 120 BPM dances featuring Professor character',
        'color': '#feca57',
        'icon': '🎓'
    },
    'special': {
        'name': 'Special Dances',
        'description': 'Unique dance combinations for special occasions',
        'color': '#ff9ff3',
        'icon': '✨'
    }
}

def get_dj_mix_command(command_key):
    """Get a specific DJ MIX command by key"""
    return DJ_MIX_COMMANDS.get(command_key)

def get_dj_mix_commands_by_category(category):
    """Get all DJ MIX commands for a specific category"""
    return {k: v for k, v in DJ_MIX_COMMANDS.items() if v['category'] == category}

def get_all_dj_mix_categories():
    """Get all available categories"""
    return DJ_MIX_CATEGORIES

def generate_dj_mix_markup(command_key):
    """Generate combined markup for audio + behavior command"""
    command = get_dj_mix_command(command_key)
    if not command:
        return None

    # Combine audio and behavior commands
    combined_markup = f"{command['audio_command']}{command['behavior_command']}"
    return combined_markup

def generate_stop_mix_markup():
    """Generate markup to stop all audio and dance behaviors"""
    # Stop all audio first
    stop_audio = '<mark name="cmd:stop,data:{+channel+:1,+fadeOutTime+:0.5}"/>'
    # Interrupt any running behaviors
    interrupt_behavior = '<mark name="cmd:interrupt"/>'
    return f"{stop_audio}{interrupt_behavior}"

def get_dj_mix_command_info(command_key):
    """Get human-readable information about a DJ MIX command"""
    command = get_dj_mix_command(command_key)
    if not command:
        return None

    category_info = DJ_MIX_CATEGORIES.get(str(command['category']), {})

    return {
        'name': command['name'],
        'description': command['description'],
        'category': command['category'],
        'category_name': category_info.get('name', 'Unknown'),
        'bpm': command['bpm'],
        'duration': command['duration'],
        'icon': category_info.get('icon', '🎵')
    }
