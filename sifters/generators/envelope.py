import numpy

class Envelope:
    
    def generate_adsr_envelope(self, length=2048, attack_time=0.25, decay_time=0.25, sustain_level=0.25, release_time=0.25):
        envelope = numpy.zeros(length)
        
        # Attack
        attack_samples = int(attack_time * length)
        envelope[:attack_samples] = numpy.linspace(0, 1, attack_samples)
        
        # Decay
        decay_samples = int(decay_time * length)
        envelope[attack_samples:attack_samples + decay_samples] = numpy.linspace(1, sustain_level, decay_samples)
        
        # Sustain
        sustain_samples = length - attack_samples - decay_samples
        envelope[attack_samples + decay_samples:attack_samples + decay_samples + sustain_samples] = sustain_level
        
        ### HOW TO CURVE THE RELEASE STAGE
        # Release
        release_samples = int(release_time * length)
        envelope[-release_samples:] = numpy.linspace(sustain_level, 0, release_samples)
        
        return envelope