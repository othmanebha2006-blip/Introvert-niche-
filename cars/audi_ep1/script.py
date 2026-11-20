# Voiceover. Each entry is one sentence: (caption text, what the voice says).
# Sentences are synthesised one by one, so every sentence's start/end time is exact.
# BEAT marks the start of a new visual beat (shot).
S = []
def beat(*sents):
    S.append(("BEAT", None))
    for s in sents:
        S.append(s if isinstance(s, tuple) else (s, s))

beat(("Audi badges, explained in under a minute.", "Audi badges, explained in under a minute."))
beat(("A is the normal car.", "A, is the normal car."),
     ("A3, A4, A6.", "A three. A four. A six."),
     ("The number just tells you how big it is.",)*2)
beat(("Q means it's an SUV.", "Q means it's an S U V."),
     ("Same rule. Q3 is small, Q7 is big.", "Same rule. Q three is small, Q seven is big."))
beat(("S is the sporty one.", "S, is the sporty one."),
     ("An S3 is an A3 with more power and firmer suspension.", "An S three, is an A three, with more power, and firmer suspension."))
beat(("RS stands for RennSport.", "R S, stands for Renn-shpoart."),
     ("That's German for racing sport.",)*2,
     ("It's the top of the range.",)*2)
beat(("And the first RS ever sold?", "And the first R S ever sold?"),
     ("An estate.",)*2,
     ("The RS2 Avant, built with Porsche, in 1994.", "The R S two Avant. Built with Porsche, in nineteen ninety-four."))
beat(("Avant is just Audi's word for estate.",)*2,
     ("Sportback means a sloping roof at the back.",)*2)
beat(("Quattro is all-wheel drive.", "Quattro, is all-wheel drive."),
     ("Audi made it famous in rallying,", "Audi made it famous in rallying."),
     ("and they still write it with a small q.", "And they still write it, with a small q."))
beat(("Now the bit nobody knows.",)*2,
     ("The number on the boot, like 35 or 45, isn't the engine size.", "The number on the boot, like thirty-five, or forty-five, isn't the engine size."),
     ("It's a power band.",)*2,
     ("Bigger number, more power.",)*2)
beat(("TFSI is a petrol turbo.", "T F S I, is a petrol turbo."),
     ("TDI is diesel.", "T D I, is diesel."),
     ("TFSI e is a plug-in hybrid.", "T F S I e, is a plug-in hybrid."),
     ("And e-tron is fully electric.", "And e-tron, is fully electric."))
beat(("S line?", "S line?"),
     ("That's just the look.",)*2,
     ("Bigger wheels, sharper bumpers, same engine.", "Bigger wheels. Sharper bumpers. Same engine."))
beat(("So S line looks fast.",)*2,
     ("S is fast.", "S, is fast."),
     ("And RS is the one you hear before you see it.", "And R S, is the one you hear, before you see it."))
