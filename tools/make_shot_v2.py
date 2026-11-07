#!/usr/bin/env python3
"""Generate a unique shot list for the 70 narration blocks (kill duplicates).

Each block gets 1-2 dedicated images (N001-A, N001-B...), with prompts drawn
from an act-specific motif bank and varied camera/lighting. No existing image
is reused, so the 160 shot slots become 160 unique pictures.

Outputs:
  films/01-illusion-frontiere/storyboard/shots-v2.json
  films/01-illusion-frontiere/storyboard/narration-map.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = ROOT / "films/01-illusion-frontiere/script/blocks.json"
SHOTS = ROOT / "films/01-illusion-frontiere/storyboard/shots-v2.json"
MAP = ROOT / "films/01-illusion-frontiere/storyboard/narration-map.json"

BANKS = {
    "PROLOGUE": [
        "A vast subterranean archive room at night, floor-to-ceiling filing cabinets disappearing into shadow, a lone woman in a wool coat seen from behind facing a pale projection screen showing a faint world map, foreground desk out of focus",
        "Extreme close-up of a blank beige paper file on a dark wooden table, a red rubber stamp beside it, a woman's hand resting on the cover, single warm desk lamp",
        "A long dark corridor lined with filing cabinets, a single neon tube flickering overhead, wet concrete floor reflecting the light, one-point perspective",
        "A film projector lens close-up, a beam of light cutting through dust in a dark room, pale screen glow at the edge of frame",
        "A metal filing drawer pulled open in a dark archive, a hand hovering over the tabs, dust in the light, burgundy glove",
        "A wall map of the world on a dark archive wall, thin red threads connecting locations, single warm lamp, deep shadows",
        "A stack of blank manila folders on a metal desk, a red stamp and ink pad, overhead lamp, dust",
        "A silhouetted archivist walking between tall cabinets, carrying a single file, cold blue backlight, volumetric haze",
        "A pale projection screen seen from an angle, blank and slightly overexposed, dark room around it, dust in the beam",
        "A close-up of a typewriter keyboard in a dark office, dust between the keys, cold blue light",
        "An empty chair facing a blank screen in a dark archive, single overhead light, deep shadow",
        "A metal cart loaded with files in a dark corridor, wheels wet on concrete, cold blue light",
        "A red wax seal and a folded letter on a dark table, single lamp, shallow depth of field",
        "A door left ajar at the end of a dark archive corridor, warm light spilling out, dust",
        "A high-angle view of the archive floor, scattered papers, open drawers, a single neon tube",
    ],
    "APPRENDRE": [
        "A toddler's hand gripping an adult finger, extreme close-up, dark apartment hallway, cold steel-blue window light",
        "A child's bare feet taking an uncertain step on a wooden floor, low angle, deep shadow, cold window light",
        "A parent's silhouette in a doorway, a small child in the foreground, faint burgundy lamp behind",
        "A dark 1970s computer room, a single green-phosphor terminal glowing, magnetic tape reels, cables, no people",
        "Punched cards scattered on a metal desk, a single lamp, dust, cold blue shadows",
        "A translucent neural-network diagram projected on a pale screen in a dark room, clean unmarked surface",
        "A toddler's face in profile, eyes wide, cold window light, the rest of the face in deep shadow",
        "A stack of children's books on a dark floor, a warm lamp, a blurred toy in the foreground",
        "An empty playground at night, a single swing moving, cold blue fog, distant streetlight",
        "A hand writing in a notebook, close-up, dim warm lamp, cold blue shadow behind",
        "A server rack in a dark room, blinking blue lights, tangled cables, cold haze",
        "A lone chair in a dark classroom, a chalkboard erased to grey, cold window light",
        "A mother's blurred hand reaching into frame, a child in the background, shallow depth of field",
        "A broken wooden toy on the floor, macro, dust, cold light from the side",
        "A door left ajar, warm light spilling into a dark hallway, a small pair of shoes",
    ],
    "MÉMOIRE": [
        "An elderly man's hands holding a faded photograph, close-up, cold hospital window light, shallow depth of field",
        "A hospital room window at night, rain on the glass, an empty bed with a burgundy blanket, cold blue",
        "Black-and-white photographs scattered on a dark table, a single warm lamp, dust, index cards",
        "A reel-to-reel tape recorder spinning, close-up, dust in the light, warm lamp, cold shadows",
        "A brain scan on a light box in a dark medical room, no labels, a radiologist's silhouette",
        "A metal filing drawer open in a dark archive, a hand hovering, dust, cold blue light",
        "An archive corridor with cabinets, a flickering neon tube, one-point perspective, wet floor",
        "A wall of photographs connected by red threads in a dark room, single lamp, pins and string",
        "A wristwatch on a bedside table at three in the morning, cold light, a glass of water",
        "An empty chair by a hospital window, rain, cold blue light, a folded blanket",
        "A stack of index cards with a red stamp, macro, dark table, single lamp",
        "A faded photograph held at the edge, fingers, dark background, shallow depth of field",
        "A mirror reflecting an empty room, dust on the glass, cold blue light, burgundy curtain",
        "A door closing at the end of a dark corridor, a strip of light under it",
        "A child's drawing pinned to a dark wall, faded paper, cold light, no readable text",
    ],
    "CORPS": [
        "A large robotic arm lifting a metal part in a dark factory, sparks falling, a worker silhouetted behind a fence",
        "A human hand with a small fresh cut on the knuckle, extreme close-up, cold side light, deep shadow",
        "A glass petri dish with living human neurons, fine translucent filaments, electrodes, cold steel-blue light, burgundy reflection",
        "A dark biotech lab at night, rows of incubators with faint green light, a scientist in a coat seen from behind, a microscope with a glowing dish",
        "A microscope with a small glowing sample, dark bench, red cable, dust, cold light",
        "Gloved hands handling a sample dish, close-up, sterile bench, cold blue light",
        "A bioreactor with tubes and pale liquid, dark lab, faint green glow, condensation",
        "A human hand and a robotic hand on a metal table, not touching, cold light, shallow depth of field",
        "A heartbeat monitor in a dark room, blue glow, cables, shallow depth of field",
        "A patient lying inside an MRI scanner, cold blue light, a radiologist's silhouette behind glass",
        "Macro close-up of human skin, pores and fine hairs, cold side light, dark background",
        "A prosthetic hand on a workbench, tools and metal shavings, dust, cold light",
        "A laboratory freezer with frosted glass, blue interior light, dark room, condensation",
        "Cables and electrodes on a wet lab bench, macro, cold blue light, a single red wire",
        "A single drop of water on a brushed metal surface, macro, cold light, deep shadow",
    ],
    "ÉMOTION": [
        "A woman lying in bed at night, her face lit by a cold phone screen, a faint smile, burgundy blanket, dark room",
        "A smartphone screen close-up in the dark, abstract message bubbles without readable text, a thumb hovering, reflections",
        "An empty armchair in a dark living room at three in the morning, a phone glowing on a low table",
        "Two empty chairs facing each other in a dark room, a single hanging bulb, cold blue and burgundy",
        "A handwritten letter on a dark table, a single warm lamp, a pen, shallow depth of field",
        "A cup of tea gone cold on a bedside table at night, cold blue light, a blurred bed",
        "A window with rain and blurred city lights, dark bedroom, cold blue and a faint warm lamp",
        "A person's silhouette at a window, back to camera, cold light, a phone glowing in their hand",
        "A phone vibrating on a wooden table, motion blur, dark room, cold screen glow",
        "A mirror reflecting an empty bed, dim light, burgundy sheet, dust",
        "A stack of letters tied with string on a dark table, dust, single warm lamp",
        "A hand reaching for a phone in the dark, close-up, cold screen light on the fingers",
        "A bedside lamp with a burgundy shade, a warm pool of light in a dark room",
        "An empty pillow with an indentation, cold morning light, dark bedroom",
        "A door left open, light from a hallway falling across a dark bedroom floor",
    ],
    "CONSCIENCE": [
        "A patient inside an MRI scanner, cold steel-blue light, a radiologist's silhouette behind glass, cables and haze",
        "A dark archive room with a tall tarnished mirror, a woman's silhouette facing it, her reflection slightly offset, pale screen glow",
        "A dark 1950s interrogation room, a wooden table, a mechanical typewriter, two empty chairs, a single hanging bulb",
        "An open empty file folder on a dark table, a blank sheet, a red stamp, a woman's hand at the edge",
        "A brain scan on a light box in a dark room, no labels, cold blue glow, a silhouette",
        "Extreme close-up of a human eye, a pale screen reflected in the iris, macro, cold light",
        "A mirror reflecting a blank projector screen in a dark room, dust, cold blue",
        "A single chair in a dark room under a spotlight, deep shadow, concrete floor",
        "A door with a red exit sign at the end of a dark corridor, cold light, haze",
        "A pendulum clock in a dark room, motion blur, dust, single warm lamp",
        "A silhouette facing a bright empty screen, back to camera, dark archive, volumetric haze",
        "A glass of water on a dark table, ripples, cold light, deep shadow",
        "A film projector beam cutting through dust in a dark room, pale screen edge",
        "A white plaster mask on a dark table, cold side light, dust, shallow depth of field",
        "A hand touching a mirror, the reflection offset and darker, cold blue light",
    ],
    "FINALE": [
        "A vast archive room seen from above, an empty projector screen glowing pale grey, a lone woman at the door with her back to us",
        "Extreme close-up of a beige personnel file on a dark wooden table, a red stamp, a woman's hand, single warm lamp",
        "A vast empty archive room after hours, drawers open, papers scattered on the floor, a blank projector screen, single neon tube",
        "A projector screen going dark, dust in the beam, a dark archive around it",
        "An archive door closing, a strip of cold light underneath, dark corridor",
        "A world map on a dark table with thin red route lines, a single lamp, no text",
        "A red stamp hitting a blank file, ink burst, macro, dark table, single lamp",
        "A silhouette walking away down a long archive corridor, cold blue light, haze",
        "A single desk lamp in a dark room, an empty chair, dust",
        "A film reel unspooling on the floor, celluloid ribbon, dust, cold light",
        "A child's drawing of a family and a machine pinned to a dark wall, faded paper, no readable text",
        "A window with first light, a dark room, dust in the air, a single chair",
        "A hand closing a file, close-up, red stamp, cold blue shadow",
        "An empty chair facing a blank screen, cold blue light, deep shadow",
        "A door opening into darkness, light from the archive spilling across the floor",
    ],
}

CAMERAS = [
    "Wide shot, 35mm anamorphic lens, deep spatial layering, foreground / subject / background",
    "Medium shot, 50mm lens, shallow depth of field, subject in the left third",
    "Close-up, 85mm lens, very shallow depth of field, quiet negative space on one side",
    "Extreme close-up, macro lens, fine texture, dark background",
    "Low angle, wide lens, subject looming against the ceiling, deep shadow",
    "High angle, wide lens, the room opening below, geometric composition",
    "Over-the-shoulder shot, 40mm lens, the subject soft in the foreground, the room sharp beyond",
    "Profile shot, 65mm lens, the face half in shadow, cold rim light",
]

LIGHTS = [
    "Cold steel-blue window light from the left, a single warm burgundy practical lamp, thin volumetric haze",
    "Pale projector glow as the only key light, deep blue-black shadows, dust in the beam",
    "A single overhead tungsten bulb, hard pool of light, the rest of the room in darkness",
    "Flickering neon from the corridor, cold blue and a faint red accent, wet concrete reflections",
    "Soft cold moonlight through haze, muted burgundy midtones, deep shadow",
    "A warm desk lamp against cold blue shadows, high contrast, film grain",
    "Dim monitor glow on skin and metal, teal shadows, a distant red emergency light",
    "Backlit silhouette against a pale screen, strong rim light, the foreground almost black",
]


def bank_for(act):
    upper = (act or "").upper()
    for key in ("PROLOGUE", "APPRENDRE", "MÉMOIRE", "CORPS", "ÉMOTION", "CONSCIENCE", "FINALE"):
        if key in upper:
            return BANKS[key]
    return BANKS["PROLOGUE"]


def main():
    blocks = json.loads(BLOCKS.read_text())["blocks"]
    shots = []
    mapping = {}
    for i, b in enumerate(blocks):
        bank = bank_for(b["act"])
        count = 1 if b["seconds"] < 8 else 2
        ids = []
        for v in range(count):
            sid = f"{b['id']}-{chr(65 + v)}"
            motif = bank[(i * 2 + v) % len(bank)]
            camera = CAMERAS[(i + v) % len(CAMERAS)]
            light = LIGHTS[(i * 3 + v) % len(LIGHTS)]
            prompt = (
                f"{motif}. {camera}. {light}. "
                "Photorealistic, one coherent physical space, a believable light source, "
                "quiet negative space for typography, clean unmarked surfaces, no text."
            )
            shots.append({
                "id": sid,
                "block": b["id"],
                "act": b["act"],
                "title": b["text"][:60],
                "duration": round(b["seconds"] / count, 3),
                "resolution": "1024px (Standard)",
                "seed": 100000 + i * 10 + v,
                "camera": "push-in" if v == 0 else "pan-right",
                "overlay": "",
                "prompt": prompt,
            })
            ids.append(sid)
        mapping[b["id"]] = ids

    SHOTS.write_text(json.dumps({
        "project": "01-illusion-frontiere",
        "batch": "v2-unique",
        "fps": 24,
        "width": 1920,
        "height": 1080,
        "note": "One dedicated image per narration block (Nxxx-A/B). No image reused.",
        "shots": shots,
    }, ensure_ascii=False, indent=2) + "\n")
    MAP.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(shots)} new shots for {len(blocks)} blocks, {len(mapping)} mappings")
    print("first:", shots[0]["id"], shots[0]["prompt"][:90])


if __name__ == "__main__":
    main()
