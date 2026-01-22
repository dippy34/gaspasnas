(function(){
    ClonerLog || (ClonerLog = console.log);
    // window.CrazyGames.SDK.game.gameplayStart();
    // window.CrazyGames.SDK.game.gameplayStop();
    // window.CrazyGames.SDK.ad.requestAd("midgame", callbacks);
    // cachedData = yield window.CrazyGames.SDK.data.getItem(cgProfileName);
    // window.CrazyGames.SDK.data.setItem(cgProfileName, JSON.stringify(a))
    // window.CrazyGames.SDK.ad.hasAdblock();


    window.CrazyGames= {
        CrazySDK: {
            getInstance: function() {
                ClonerLog("CrazyGames.CrazySDK.getInstance");

                this.requestAd=  async function(type = "midgame") {
                    setTimeout(() => {
                        this.callListeners && this.callListeners("adFinished", { adType: type });
                    }, 100);
                    ClonerLog("CrazyGames.CrazySDK.getInstance.requestAd");
                    return Promise.resolve();
                };

                this.requestBanner = async function() {
                    ClonerLog("CrazyGames.CrazySDK.getInstance.requestBanner");
                    return Promise.resolve();
                };

                this.postMessage = function(type, data) {
                    ClonerLog("CrazyGames.CrazySDK.getInstance.postMessage", type, data);
                    this.callListeners?.("adFinished", { adType: data?.adType });
                    return;
                }
            }
        },
        SDK: {
            init: function() {
                ClonerLog("CrazyGames.SDK.init", arguments);
                return Promise.resolve();
            },
            user: {
                addAuthListener: function() {
                    ClonerLog("CrazyGames.SDK.user.addAuthListener", arguments);
                }
            },
            game: {
                gameplayStart: function() {
                    ClonerLog("CrazyGames.SDK.game.gameplayStart", arguments);
                },
                gameplayStop: function() {
                    ClonerLog("CrazyGames.SDK.game.gameplayStop", arguments);
                },
                loadingStart: function() {
                    ClonerLog("CrazyGames.SDK.game.loadingStart", arguments);
                },
                loadingStop: function() {
                    ClonerLog("CrazyGames.SDK.game.loadingStop", arguments);
                },
            },
            ad: {
                requestAd: function(type, callbacks) {
                    ClonerLog("CrazyGames.SDK.ad.requestAd", type, callbacks);
                    const adFinished= callbacks?.["adFinished"];
                    // const adError= callbacks?.["adError"];
                    const adStarted= callbacks?.["adStarted"];
                    adStarted && adStarted();
                    return ClonerAd(adFinished);
                    // adFinished && adFinished();
                },
                hasAdblock: function() {
                    ClonerLog("CrazyGames.SDK.ad.hasAdblock", arguments);
                    return Promise.resolve();
                }
            },
            data: {
                getItem: function() {
                    ClonerLog("CrazyGames.SDK.data.getItem", arguments);
                    return "{}";
                },
                setItem: function() {
                    ClonerLog("CrazyGames.SDK.data.setItem", arguments);
                },
                syncUnityGameData: function() {
                    ClonerLog("CrazyGames.SDK.data.syncUnityGameData", arguments);
                }
            }
        }
    }
})();
