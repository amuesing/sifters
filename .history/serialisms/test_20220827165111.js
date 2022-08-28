function noteToFreq(note) {
    let a = 440; 
    console.log() (a / 32) * (2 ** ((note - 9) / 12));
}

console.log(noteToFreq(72))