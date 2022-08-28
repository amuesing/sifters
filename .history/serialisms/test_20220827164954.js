function noteToFreq(note) {
    let a = 440; //frequency of A (coomon value is 440Hz)
    return (a / 32) * (2 ** ((note - 9) / 12));
}

console.log(noteToFreq(72))