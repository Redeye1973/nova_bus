// Genereer 1 seconde laser sound, save als WAV (NRT mode)
(
s.boot;
s.waitForBoot({
    var b = Buffer.alloc(s, s.sampleRate * 1, 1);
    var synth = {
        var freq = XLine.kr(2000, 200, 0.3);
        var sig = SinOsc.ar(freq) * EnvGen.ar(Env.perc(0.01, 0.3), doneAction: 2);
        sig * 0.3;
    };
    
    Score.recordNRT(
        list: [[0.0, ['/d_recv', SynthDef("laser", synth).asBytes]],
               [0.0, ['/s_new', "laser", 1000, 0, 0]],
               [1.0, [0]]],
        oscFilePath: "L:/!Nova V2/tests/audio/laser.osc",
        outputFilePath: "L:/!Nova V2/tests/audio/laser.wav",
        sampleRate: 44100,
        headerFormat: "WAV",
        sampleFormat: "int16",
        action: { "Done".postln; 0.exit }
    );
});
)
