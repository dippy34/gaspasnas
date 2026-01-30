function onwindowload(){
  LaggedAPI.init();
}
var timeplaying;
function ontick(){}
function winlevel(lvl){

console.log("won: ", lvl);

var api_awards=[];

if(lvl>4){
    api_awards.push("blob_runnertwd_dxpjx001");
}
if(lvl>9){
    api_awards.push("blob_runnertwd_dxpjx002");
}
if(lvl>14){
    api_awards.push("blob_runnertwd_dxpjx003");
}

if(api_awards.length>0){
  LaggedAPI.Achievements.save(api_awards, function(response) {
  if(response.success) {
  console.log('achievement saved')
  }else {
  console.log(response.errormsg);
  }
  });
}

LaggedAPI.APIAds.show(function() {console.log("ad completed");});

}
