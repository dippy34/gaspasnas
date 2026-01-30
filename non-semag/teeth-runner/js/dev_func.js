"use strict";
//time in seconds from window.onload
var time_playing = -1;
function on_window_load() {
    console.log("on_window_load");
}
function on_press_run() {
    console.log("on_press_run");
}

//score comes with decimals , use Math.floor o Math.round.
function on_game_tick(score) {
   // console.log(time_playing+" "+score);
}

function on_lose(score) {

  LaggedAPI.APIAds.show('interstitial','teeth-runner','teeth-runner-game.png',function(response) {
if(response.success) {
console.log('ad done');
}else {
console.log('ad error, continue');
}
});

}

var bestScore=0;
function on_win(score) {
    //console.log("won level, level: ", game.LEVEL);

if(score>bestScore){
  bestScore=score;

  var boardinfo={};
boardinfo.score=Math.round(score);
boardinfo.board="teeth_runner_hsbdgto";
LaggedAPI.Scores.save(boardinfo, function(response) {
if(response.success) {
console.log('high score saved')
}else {
console.log(response.errormsg);
}
});
}

var ach=false;
var ach_numb=[];
if(game.LEVEL>19){
ach=true;
ach_numb.push("teeth_runner_wqnrf004");
}
if(game.LEVEL>14){
ach=true;
ach_numb.push("teeth_runner_wqnrf003");
}
if(game.LEVEL>9){
ach=true;
ach_numb.push("teeth_runner_wqnrf002");
}
if(game.LEVEL>4){
ach=true;
ach_numb.push("teeth_runner_wqnrf001");
}
if(ach){
LaggedAPI.Achievements.save(ach_numb, function(response) {
if(response.success) {
console.log('achievement saved')
}else {
console.log(response.errormsg);
}
});
}


LaggedAPI.APIAds.show('interstitial','teeth-runner','teeth-runner-game.png',function(response) {
if(response.success) {
console.log('ad done');
}else {
console.log('ad error, continue');
}
});

}
