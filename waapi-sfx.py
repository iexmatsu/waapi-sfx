from waapi import WaapiClient
from random import uniform, randrange, choice

# Connect (default URL)
client = WaapiClient()

# get all ShareSet effects from the project
effects = client.call("ak.wwise.core.object.get", {"waql": "$ from type effect where parent != null"})["return"]
    

def RandomEffect():
    # return the id of one of the ShareSet effect from the project
    return choice(effects)['id']

def ADSR(property, a,d,s,r, y_min, y_max, stop):
    # Create a RTPC entry with custom ADSR envelope object
    return {
        "type": "RTPC",
        "name": "",
        "@Curve": {
            "type": "Curve",
            "points": [
                {
                    "x": 0,
                    "y": y_min,
                    "shape": "Linear"
                },
                {
                    "x": 1,
                    "y": y_max,
                    "shape": "Linear"
                }
            ]
        },
        "@PropertyName": property,
        "@ControlInput": {
            # Envelope properties
            "type":"ModulatorEnvelope",
            "name":"ENV",
            "@EnvelopeAttackTime": a,
            "@EnvelopeAutoRelease": True,
            "@EnvelopeStopPlayback": stop,
            "@EnvelopeDecayTime": d,
            "@EnvelopeReleaseTime": r,
            "@EnvelopeSustainTime": s
        }
    }

def LFO(property, freq, y_min, y_max):
    # Create a RTPC entry with a custom LFO modulator
    return {
        "type": "RTPC",
        "name": "",
        "@Curve": {
            "type": "Curve",
            # "@Flags": 3,
            "points": [
                {
                    "x": 0,
                    "y": y_min,
                    "shape": "Linear"
                },
                {
                    "x": 1,
                    "y": y_max,
                    "shape": "Linear"
                }
            ]
        },
        "@PropertyName": property,
        "@ControlInput": {
            # LFO properties
            "type":"ModulatorLfo",
            "name":"LFO",
            "@LfoAttack": 0,
            "@LfoDepth": uniform(0,100),
            "@LfoFrequency": freq,
            "@LfoWaveform": randrange(0,6),
            "@LfoPWM": uniform(10,90)
        }
    }

def Random(property, y_min, y_max):
    # Create a RTPC entry with a custom Random LFO modulator
    return {
        "type": "RTPC",
        "name": "",
        "@Curve": {
            "type": "Curve",
            "points": [
                {
                    "x": 0,
                    "y": y_min,
                    "shape": "Linear"
                },
                {
                    "x": 1,
                    "y": y_max,
                    "shape": "Linear"
                }
            ]
        },
        "@PropertyName": property,
        "@ControlInput": {
            "type":"ModulatorLfo",
            "name":"RAND",
            "@LfoWaveform": 5,
            "@LfoFrequency":0.01
        }
    }

def RandomPoints(x_min, x_max, y_min, y_max, count):
    # Return an array of random points
    points = [
        {
            "x": x_min,
            "y": uniform(y_min, y_max),
            "shape": "Linear"
        },
        {
            "x": x_max,
            "y": uniform(y_min, y_max),
            "shape": "Linear"
        }
    ]
    for x in range(0,count-2):
        points.insert(1+x,
            {
                "x": uniform(x_min, x_max),
                "y": uniform(y_min, y_max),
                "shape": "Linear"
            })

    points.sort(key=lambda p:p["x"])
    return points

def RandomTimeCurve(property, duration, y_min, y_max, count):
    # Return a RTPC entry with random time curve
    return {
        "type": "RTPC",
        "name": "",
        "@Curve": {
            "type": "Curve",
            "points": RandomPoints(0, duration, y_min, y_max, count)
        },
        "@PropertyName": property,
        "@ControlInput": {
            # Time modulator properties
            "type":"ModulatorTime",
            "name":"TimeMod",
            "@TimeModDuration": duration,
            "@EnvelopeStopPlayback": False
        }
    }

def Modulation(property, duration, y_min, y_max):
    # Create a random modulation RTPC entry
    
    pick = randrange(0,4)
    start_ratio = uniform(0,1)
    range = (y_max-y_min)
    y_min = y_min + range*start_ratio
    y_max = y_max - range*(1-start_ratio)*uniform(0,1)

    if pick == 0:
        return RandomTimeCurve(property, duration, y_min, y_max, randrange(2,9))
    elif pick == 1:
        return Random(property, y_min, y_max)
    elif pick == 2:
        return LFO(property, uniform(0.01, 30), y_min, y_max)
    elif pick == 3:
        attack = duration - uniform(0,duration)
        release = duration - attack
        return ADSR(property, attack, 0, 0, release, y_min, y_max, False)

def Sound(i, sustain):
    # Return a Sound SFX object with a Synth One source

    attack = uniform(0.01, sustain)
    decay = uniform(0.01, sustain)
    release = uniform(0.01, sustain)
    duration = attack + decay + sustain + release

    return {
        "type":"Sound",
        "name":"FX" + str(i),
        "children":[
            {
                "type":"SourcePlugin",
                "name":"WSFX",
                "classId": 9699330, # synth one: https://www.audiokinetic.com/library/edge/?source=SDK&id=wwiseobject_source_wwise_synth_one.html
                "@BaseFrequency": uniform(100, 1000),
                "@Osc1Waveform": randrange(0,4),
                "@Osc2Waveform": randrange(0,4),
                "@NoiseShape": randrange(0,4),
                "@NoiseLevel": uniform(-12, 0),
                "@RTPC":[
                    Modulation("Osc1Transpose", duration, -1200, 1200),
                    Modulation("Osc2Transpose", duration, -1200, 1200),
                    Modulation("NoiseLevel", duration, -96, 6),
                    Modulation("Osc1Pwm", duration, 1, 99),
                    Modulation("Osc2Pwm", duration, 1, 99),
                    Modulation("FmAmount", duration, 0, 100),
                ],
            }
        ],
        "@Effect0": RandomEffect(),
        "@RTPC":[
            ADSR("Volume", attack, decay, sustain, release, -96, 0, True),
            Modulation("Lowpass", duration, 0, 20),
            Modulation("Highpass", duration, 0, 20),
        ],
    }

def Generate(num_sounds):
    # Create the sounds using ak.wwise.core.object.set
    
    args = {
        "objects": [
            {
                "object": "\\Actor-Mixer Hierarchy\\Default Work Unit",
                "children": list(map( lambda i : Sound(i, uniform(0.1, 3)), range(1,num_sounds+1)))
            },

        ],
        "onNameConflict": "merge",
        "listMode":"replaceAll"
    }

    # Call WAAPI to create the objects
    client.call("ak.wwise.core.object.set", args)

Generate(16)

# Disconnect
client.disconnect()
