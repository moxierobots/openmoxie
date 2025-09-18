"""
Behavior configuration and mappings for Moxie robot behaviors
"""

# Quick action to behavior mappings
QUICK_ACTION_MAPPINGS = {
    'celebrate': 'Bht_Spin_360',
    'dance': 'Bht_Circle_motion',
    'laugh': 'Bht_Vg_Laugh_Big_Fourcount',
    'wave': 'Bht_Wait_Hug',
    'point': 'Bht_Photo_pose_Curious',
    'think': 'Bht_Vg_Hmm_Confused_Sustained',
    'surprise': 'Bht_Startled',
    'bow': 'Bht_Turn_Away',
    'snore': 'Bht_Vg_Snore_Heavy'
}

# Base behavior markup template
BEHAVIOR_MARKUP_TEMPLATE = '''<mark name="cmd:behaviour-tree,data:{{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+{behavior_name}+,   +Track+:++ }}"/>'''

# Enhanced behavior mappings with full markup commands
BEHAVIOR_COMMANDS = {
    'Bht_Vg_Laugh_Belly': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Laugh_Belly+,   +Track+:++ }"/>',
    'Bht_Vg_Laugh_Big': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Laugh_Big+,   +Track+:++ }"/>',
    'Bht_Vg_Laugh_Big_Fourcount': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+sfx_moxie_laugh_loop+,+LoopSound+:true,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:60.0,+AudioTimelineField+:+none+}"/><mark name="cmd:behaviour-tree,data:{   +transition+:0.0,   +duration+:4.0,   +repeat+:15,   +layerBlendInTime+:0.0,   +layerBlendOutTime+:0.0,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Laugh_Big_Fourcount+,   +Track+:++ }"/>',
    'Bht_Vg_Laugh_Big_Fourcount_Loop': '<mark name="cmd:playaudio,data:{+SoundToPlay+:+sfx_moxie_laugh_loop+,+LoopSound+:true,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:true,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:1.0,+FadeInTime+:0.0,+FadeOutTime+:90.0,+AudioTimelineField+:+none+}"/><mark name="cmd:behaviour-tree,data:{   +transition+:0.0,   +duration+:3.0,   +repeat+:30,   +layerBlendInTime+:0.0,   +layerBlendOutTime+:0.0,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Laugh_Big_Fourcount+,   +Track+:++ }"/>',
    'Bht_Vg_Laugh_Mischief': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Laugh_Mischief+,   +Track+:++ }"/>',
    'Bht_Vg_Laugh_Nervous': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Laugh_Nervous+,   +Track+:++ }"/>',
    'Bht_Vg_Snore_Light': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Snore_Light+,   +Track+:++ }"/>',
    'Bht_Vg_Snore_Heavy': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Snore_Heavy+,   +Track+:++ }"/>',
    'Bht_Vg_Shiver_Sustained': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Shiver_Sustained+,   +Track+:++ }"/>',
    'Bht_Vg_Ooo_Cringe': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Ooo_Cringe+,   +Track+:++ }"/>',
    'Bht_Vg_Oh_Eureka': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Oh_Eureka+,   +Track+:++ }"/>',
    'Bht_Vg_Hmm_Confused_Sustained': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Hmm_Confused_Sustained+,   +Track+:++ }"/>',
    'Bht_Vg_Clear_Throat': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Clear_Throat+,   +Track+:++ }"/>',
    'Bht_Vg_Gasp': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Gasp+,   +Track+:++ }"/>',
    'Bht_Vg_Gulp': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Gulp+,   +Track+:++ }"/>',
    'Bht_Spin_360': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Spin_360+,   +Track+:++ }"/>',
    'Bht_Photo_pose_Curious': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Photo_pose_Curious+,   +Track+:++ }"/>',
    'Bht_Turn_Away': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Turn_Away+,   +Track+:++ }"/>',
    'Bht_Startled': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Startled+,   +Track+:++ }"/>',
    'Bht_Circle_motion': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Circle_motion+,   +Track+:++ }"/>',
    'Bht_Wait_Hug': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Wait_Hug+,   +Track+:++ }"/>',
    'Bht_sigh_relief': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_sigh_relief+,   +Track+:++ }"/>',
    'Bht_yawn_big': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_yawn_big+,   +Track+:++ }"/>',
    'bht_accept_hug': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+bht_accept_hug+,   +Track+:++ }"/>',
    'bht_clearthroat': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+bht_clearthroat+,   +Track+:++ }"/>',
    'Bht_Back_and_forth_arm_wave': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:3.0,   +repeat+:2,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Back_and_forth_arm_wave+,   +Track+:++ }"/>',
    'Bht_raspberry': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:1.5,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_raspberry+,   +Track+:++ }"/>',
    'Bht_raspberry_long': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:3.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_raspberry_long+,   +Track+:++ }"/>',
    'Bht_Vg_gasp': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:1.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_gasp+,   +Track+:++ }"/>',
    'Bht_Vg_cough': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:1.5,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_cough+,   +Track+:++ }"/>',
    'Bht_Vg_gulp': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:1.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_gulp+,   +Track+:++ }"/>',
    'Bht_Wing_Flap': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Wing_Flap+,   +Track+:++ }"/>',
    'Bht_Vg_Psst': '<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:1.0,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:false,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Psst+,   +Track+:++ }"/>',
    # Add more behavioral commands as needed
}

# Predefined preset combinations
BEHAVIOR_PRESETS = {
    'greeting': [
        ('speak', {'text': 'Hello there! How are you doing today?', 'mood': 'happy', 'intensity': 0.7}),
        ('behavior', {'behavior_name': 'Bht_Wait_Hug'})
    ],
    'party': [
        ('sound_effect', {'sound_name': 'sfxmm_incoming02', 'volume': 0.8}),
        ('behavior', {'behavior_name': 'Bht_Vg_Laugh_Big'}),
        ('behavior', {'behavior_name': 'Bht_Spin_360'}),
        ('speak', {'text': "Party time! Let's celebrate!", 'mood': 'excited', 'intensity': 0.9})
    ],
    'calm': [
        ('behavior', {'behavior_name': 'Bht_sigh_relief'}),
        ('speak', {'text': "Let's take a deep breath and relax.", 'mood': 'neutral', 'intensity': 0.3}),
        ('behavior', {'behavior_name': 'Bht_yawn_big'})
    ],
    'energetic': [
        ('speak', {'text': "Let's get energized! Are you ready?", 'mood': 'excited', 'intensity': 0.8}),
        ('behavior', {'behavior_name': 'Bht_Vg_Oh_Eureka'}),
        ('behavior', {'behavior_name': 'Bht_Circle_motion'})
    ],
    'welcome_message': [
        ('sequence', {'sequence_name': 'welcome_test'})
    ],
    'dj_session': [
        ('speak', {'text': "Let's get this party started! DJ Moxie in the house!", 'mood': 'excited', 'intensity': 0.9}),
        ('behavior', {'behavior_name': 'Bht_Back_and_forth_arm_wave'}),
        ('sound_effect', {'sound_name': 'sfxmm_incoming02', 'volume': 0.9}),
        ('behavior', {'behavior_name': 'Bht_Spin_360'}),
        ('speak', {'text': "Feel the beat! Let's dance together!", 'mood': 'excited', 'intensity': 0.8})
    ],
    'beat_match': [
        ('behavior', {'behavior_name': 'Bht_Vg_Oh_Eureka'}),
        ('speak', {'text': "Perfect beat match! The rhythm is just right!", 'mood': 'happy', 'intensity': 0.7}),
        ('behavior', {'behavior_name': 'Bht_Circle_motion'}),
        ('sound_effect', {'sound_name': 'sfxmm_incoming02', 'volume': 0.8}),
        ('behavior', {'behavior_name': 'Bht_raspberry'})
    ],
}


def get_behavior_markup(behavior_name: str) -> str:
    """
    Get behavior markup for a given behavior name
    """
    # Use the predefined command if available
    if behavior_name in BEHAVIOR_COMMANDS:
        return BEHAVIOR_COMMANDS[behavior_name]

    # Otherwise generate from template
    return BEHAVIOR_MARKUP_TEMPLATE.format(behavior_name=behavior_name)


def get_quick_action_behavior(action: str) -> str:
    """
    Get behavior name for a quick action
    """
    return QUICK_ACTION_MAPPINGS.get(action, 'Gesture_None')


def get_preset_actions(preset_name: str) -> list:
    """
    Get preset action sequence
    """
    return BEHAVIOR_PRESETS.get(preset_name, [])


def get_sound_effect_markup(sound_name: str, volume: float = 0.75) -> str:
    """
    Generate sound effect markup
    """
    return f'<mark name="cmd:playaudio,data:{{+SoundToPlay+:+{sound_name}+,+LoopSound+:false,+playInBackground+:false,+channel+:1,+ReplaceCurrentSound+:false,+PlayImmediate+:true,+ForceQueue+:false,+Volume+:{volume},+FadeInTime+:0.0,+FadeOutTime+:2.0,+AudioTimelineField+:+none+}}"/>'


def get_pause_markup(seconds: float = 1.0) -> str:
    """
    Generate pause markup for timing between sequences
    """
    return f'{{"break":{{"time":"{seconds}s"}}}}'


def get_sequence_markup(sequence_name: str) -> str:
    """
    Generate complete sequence markup for predefined sequences
    """
    sequences = {
        'welcome_test': create_welcome_test_sequence()
    }

    return sequences.get(sequence_name, '')


def create_welcome_test_sequence() -> str:
    """
    Create the welcome test sequence: wave -> clear throat -> welcome speech
    """
    # Use proper behavior markup format for telehealth
    welcome_sequence = '''
<mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.5,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:true,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Wait_Hug+,   +Track+:++ }"/> <break time="1s"/> <mark name="cmd:behaviour-tree,data:{   +transition+:0.3,   +duration+:2.5,   +repeat+:1,   +layerBlendInTime+:0.4,   +layerBlendOutTime+:0.4,   +blocking+:true,   +action+:0,   +eventName+:+Gesture_None+,   +category+:+None+,   +behaviour+:+Bht_Vg_Clear_Throat+,   +Track+:++ }"/> <break time="1s"/> Welcome my friends! Your love and stories make me so happy! <break time="1s"/> Now you can talk with me directly. I can't wait to see what you share with me!
    '''.strip()

    return welcome_sequence

def create_laugh_60_second_sequence():
    """
    Create a 60-second laugh sequence using rapid-fire Bht_Vg_Laugh_Big_Fourcount commands
    """
    # Optimize timing: Each laugh 1.5s + 0.5s break = 2.0s per cycle
    # 30 cycles = exactly 60 seconds
    laugh_markup = '<mark name="cmd:behaviour-tree,data:{+transition+:0.1,+duration+:1.5,+repeat+:1,+layerBlendInTime+:0.1,+layerBlendOutTime+:0.1,+blocking+:false,+action+:0,+eventName+:+Gesture_None+,+category+:+None+,+behaviour+:+Bht_Vg_Laugh_Big_Fourcount+,+Track+:++}"/>'

    # Create sequence with proper breaks between laughs
    sequence_parts = []
    for i in range(30):  # 30 laughs over 60 seconds
        sequence_parts.append(laugh_markup)
        if i < 29:  # Don't add break after the last one
            sequence_parts.append('<break time="0.5s"/>')

    return ' '.join(sequence_parts)
