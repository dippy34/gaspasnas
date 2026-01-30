function game_load() {
    BABYLON.SceneLoader.Load("3d/", "root_game.babylon", engine, function (sc) {
        game.files_count = 2;
        game.files_loaded = 0;
        scene = sc;
        //asset loader
        var assetsManager = new BABYLON.AssetsManager(scene);
        var task1 = assetsManager.addHDRCubeTextureTask("hrd1", "3d/env_min.hdr", 128);
        task1.onSuccess = function (e) {
            game.envtext = e.texture;
        };
        assetsManager.load();
        assetsManager.onFinish = function () {
            game_file_loaded();
        };
        game.file_loaded();
    });
}
function game_file_loaded() {
    game.files_loaded++;
    //////////////////////////////
    //////////////////////////////
    //////////////////////////////
    //////////////////////////////
    if (game.files_count == game.files_loaded) {
        game.VELOCITY = 0;
        game.TOUCHING = false;
        game.PLAYING = false;
        game.LEVEL = BABYLON.DataStorage.ReadNumber(SAVE_NAME + "LEVEL", 1);
        game.SCORE = 0;
        var gravityVector = new BABYLON.Vector3(0, -9.81, 0);
        var physicsPlugin = new BABYLON.AmmoJSPlugin();
        scene.enablePhysics(gravityVector, physicsPlugin);
        level_generator.init();
        gui.load();
        document.getElementById("lock_loader").style.visibility = "hidden";
        // Fog
        var color_ = "#ffffff";
        scene.fogMode = BABYLON.Scene.FOGMODE_LINEAR;
        scene.fogColor = BABYLON.Color3.FromHexString(color_);
        scene.fogDensity = 0.01;
        scene.fogStart = 30;
        scene.fogEnd = 33;
        scene.environmentTexture = game.envtext;
        scene.environmentIntensity = 1;
        scene.clearColor = new BABYLON.Color4(1, 1, 1, 1);
        game.char11 = scene.getMeshByID("char11");
        game.char11.position.x = -10000;
        game.char12 = scene.getMeshByID("char12");
        game.char12.position.x = -10000;
        game.char13 = scene.getMeshByID("char13");
        game.char13.position.x = -10000;
        game.char21 = scene.getMeshByID("char21");
        game.char21.position.x = -10000;
        game.char22 = scene.getMeshByID("char22");
        game.char22.position.x = -10000;
        game.char23 = scene.getMeshByID("char23");
        game.char23.position.x = -10000;
        game.brush = scene.getMeshByID("brush");
        game.checker_creator = scene.getMeshByID("checker_creator");
        game.creator = scene.getMeshByID("creator");
        game.creator.isVisible = false;
        game.rotater = scene.getMeshByID("rotater");
        game.position = scene.getMeshByID("position");
        game.position.visibility = 0;
        game.ray_origin = scene.getMeshByID("ray_origin");
        game.ray_origin.isVisible = false;
        game.ray = scene.getMeshByName("ray");
        game.ray.isVisible = false;
        game.checker_dispose = scene.getMeshByName("checker_dispose");
        game.checker_dispose.isVisible = false;
        game.checker = scene.getMeshByName("checker");
        game.cartel = scene.getMeshByName("cartel");
        game.obstacle = scene.getMeshByName("obstacle");
        game.obstacle.position.z = -10000;
        game.paste = scene.getMeshByName("paste");
        game.poop = scene.getMeshByName("poop");
        game.poop.position.x = -10000;
        game.win = scene.getMeshByName("win");
        game.win.position.z = -10000;
        game.win_coll = scene.getMeshByName("win_coll");
        game.win_coll.isVisible = false;
        game.brush_poop = scene.getMeshByName("brush_poop");
        game.brush_poop.isVisible = false;
        game.particle = new BABYLON.ParticleSystem("particles", 1000, scene);
        game.particle.particleTexture = new BABYLON.Texture("images/circle_texture.png", scene);
        game.particle.emitter = game.brush;
        game.particle.emitRate = 250;
        game.particle.start();
        game.particle.minSize = 0.3;
        game.particle.maxSize = 0.4;
        game.particle.minEmitPower = 0.1;
        game.particle.maxEmitPower = 0.3;
        game.particle.maxLifeTime = 1.5;
        game.particle.minLifeTime = 2;
        game.particle.blendMode = 1;
        game.particle.color1 = BABYLON.Color4.FromHexString("#ffffffff");
        game.particle.color2 = BABYLON.Color4.FromHexString("#ffffffff");
        game.particle.colorDead = BABYLON.Color4.FromHexString("#ffffff00");
        game.particle.createBoxEmitter(new BABYLON.Vector3(-3, 2.5, 3), new BABYLON.Vector3(3, 2.5, -3), new BABYLON.Vector3(-0.3, -0.1, -0.5), new BABYLON.Vector3(0.3, -0.2, 0.5));
        game.t_cleaned = scene.getMaterialByName("t_clean");
        game.m_ok = scene.getMaterialByName("ok");
        scene.onPointerMove = function () {
        };
        scene.onPointerDown = function () {
            game.TOUCHING = true;
        };
        scene.onPointerUp = function () {
            game.TOUCHING = false;
        };
        engine.runRenderLoop(game.tick);
    }
}
function game_tick() {
    time_playing = (new Date().getTime() / 1000) - time_start;
    on_game_tick(game.SCORE);
    gui.txt.text = scene.meshes.length.toString() + " meshes " + Math.round(engine.getFps()) + " fps";
    var dt = engine.getDeltaTime() / 16;
    dt = Math.min(dt, 3);
    gui.txt_add_score.alpha -= dt / 10;
    gui.txt_add_score.alpha = Math.max(gui.txt_add_score.alpha, 0);
    game.position.position.z += 0.06 * game.VELOCITY * dt * 1.15;
    level_generator.tick();
    var origin = game.ray_origin.absolutePosition;
    var forward = new BABYLON.Vector3(0, -1, 0);
    var direction = forward.subtract(origin);
    var length = 50;
    var ray = new BABYLON.Ray(origin, new BABYLON.Vector3(0, -1, 0), length);
    var hit = scene.pickWithRay(ray);
    if (game.TOUCHING && game.PLAYING) {
        game.brush.setParent(game.ray);
    }
    else {
        game.sounds.brush.stop();
        game.brush.setParent(game.position);
        if (game.PLAYING)
            game.brush.position.y += 0.008 * dt * 16;
        if (game.brush.position.y > 1.5) {
            game.brush.position.y = 1.5;
        }
        game.particle.emitRate = 0;
    }
    if (hit.pickedMesh) {
        game.ray.position = hit.pickedPoint;
        if (game.TOUCHING && game.PLAYING) {
            game.brush.position.y -= 0.008 * dt * 16;
            if (game.brush.position.y < 0) {
                game.brush.position.y = 0;
                game.particle.emitRate = 250;
                if (!game.sounds.brush.isPlaying) {
                    BABYLON.Engine.audioEngine.unlock();
                    game.sounds.brush.play();
                    game.sounds.brush.loop = true;
                }
            }
        }
        else {
        }
    }
    scene.getMeshesByTags("loopeable").forEach(function (e) {
        var tags = BABYLON.Tags.GetTags(e, false);
        if (tags.char) {
            game.checker_dispose.setParent(null);
            if (game.checker.intersectsMesh(e) && game.brush.position.y < 0.01) {
                e.metadata.cleaned += dt * 16 * game.VELOCITY;
                if (e.metadata.cleaned > 400 &&
                    !e.metadata.ready) {
                    var score_to_add = 0;
                    e.metadata.ready = true;
                    var newcartel = game.cartel.clone("newcartel", e);
                    var reset_vel = true;
                    newcartel.scaling.x = 0.1;
                    BABYLON.Animation.CreateAndStartAnimation("scaling", newcartel, "scaling", 60, 5, newcartel.scaling.clone(), new BABYLON.Vector3(1, 1, 1), BABYLON.Animation.ANIMATIONLOOPMODE_CONSTANT);
                    newcartel.position = BABYLON.Vector3.Zero();
                    if ((e.metadata.type == "man" && game.CURRENT == "paste") ||
                        (e.metadata.type == "ogre" && game.CURRENT == "poop")) {
                        game.sounds.up.play();
                        score_to_add = 1;
                        newcartel.getChildMeshes()[0].material = game.m_ok;
                        game.VELOCITY *= 1.15;
                        game.VELOCITY = Math.min(game.VELOCITY, 2);
                        reset_vel = false;
                    }
                    else {
                        game.sounds.down.play();
                    }
                    if (reset_vel) {
                        game.VELOCITY = 1 / 1.15;
                    }
                    if (game.CURRENT == "paste") {
                        e.metadata.teeth.material = game.t_cleaned;
                    }
                    if (game.CURRENT == "poop") {
                        e.metadata.teeth.material = game.poop.material;
                    }
                    game.SCORE += 10 * game.VELOCITY * score_to_add;
                    gui.txt_add_score.text = "+" + Math.floor(10 * game.VELOCITY * score_to_add);
                    gui.txt_add_score.alpha = 10;
                    gui.txt_score.text = Math.floor(game.SCORE).toString();
                }
            }
            if (e.position.z < game.checker_dispose.position.z) {
                e.dispose();
            }
            game.checker_dispose.setParent(game.position);
        }
        if (tags.poop && game.brush.intersectsMesh(e)) {
            game.brush_poop.isVisible = true;
            game.particle.color1 = BABYLON.Color4.FromHexString("#52411dff");
            game.particle.color2 = BABYLON.Color4.FromHexString("#52411dff");
            game.particle.colorDead = BABYLON.Color4.FromHexString("#52411d00");
            e.visibility = 0.5;
            game.CURRENT = "poop";
        }
        if (tags.paste && game.brush.intersectsMesh(e)) {
            game.brush_poop.isVisible = false;
            game.particle.color1 = BABYLON.Color4.FromHexString("#ffffffff");
            game.particle.color2 = BABYLON.Color4.FromHexString("#ffffffff");
            game.particle.colorDead = BABYLON.Color4.FromHexString("#ffffff00");
            e.visibility = 0.5;
            game.CURRENT = "paste";
        }
        if (tags.obstacle && game.brush.intersectsMesh(e)) {
            if (game.PLAYING) {
                on_lose(game.SCORE);
                game.sounds.motor.stop();
                game.sounds.brush.stop();
                gui.avd.addControl(gui.btn_reset);
                game.sounds.punch.play();
                var frameRate = 10;
                var xSlide = new BABYLON.Animation("xSlide", "position.x", frameRate, BABYLON.Animation.ANIMATIONTYPE_FLOAT, BABYLON.Animation.ANIMATIONLOOPMODE_CYCLE);
                var keyFrames = [];
                keyFrames.push({
                    frame: 0,
                    value: game.brush.position.x - 200000
                });
                keyFrames.push({
                    frame: 100,
                    value: game.brush.position.x - 200000
                });
                keyFrames.push({
                    frame: 101,
                    value: game.brush.position.x
                });
                keyFrames.push({
                    frame: 200,
                    value: game.brush.position.x
                });
                xSlide.setKeys(keyFrames);
                game.brush.animations.push(xSlide);
                var myAnim = scene.beginAnimation(game.brush, 0, 200, true, 100);
            }
            game.PLAYING = false;
            game.VELOCITY = 0;
            if (!game.PLAYING) {
                game.position.position.z -= 0.1;
            }
        }
    });
    if (game.brush.intersectsMesh(game.win_coll) && game.PLAYING) {
        on_win(game.SCORE);
        game.sounds.motor.stop();
        game.sounds.brush.stop();
        gui.avd.addControl(gui.btn_next);
        if (game.SCORE > BABYLON.DataStorage.ReadNumber(SAVE_NAME + "RECORD", 0)) {
            gui.star_new.alpha = 1;
        }
        BABYLON.DataStorage.WriteNumber(SAVE_NAME + "LEVEL", game.LEVEL + 1);
        BABYLON.DataStorage.WriteNumber(SAVE_NAME + "RECORD", Math.max(game.SCORE, BABYLON.DataStorage.ReadNumber(SAVE_NAME + "RECORD", 0)));
        game.VELOCITY = 0;
        game.PLAYING = false;
        function create_part(x_) {
            var part = new BABYLON.ParticleSystem("particles", 100, scene);
            part.particleTexture = new BABYLON.Texture("images/circle_texture.png", scene);
            part.emitter = game.win_coll.absolutePosition.clone();
            part.emitter.y = 0;
            part.emitter.x += x_;
            part.color1 = BABYLON.Color4.FromHexString("#ff0000ff");
            part.color2 = BABYLON.Color4.FromHexString("#00ff00ff");
            part.colorDead = BABYLON.Color4.FromHexString("#ffffff00");
            part.maxSize = 0.2;
            part.minSize = 0.1;
            part.maxEmitPower = 0.3;
            part.minEmitPower = 0.2;
            part.maxEmitBox = new BABYLON.Vector3(0, 0, 0);
            part.minEmitBox = new BABYLON.Vector3(0, 0, 0);
            part.direction1 = new BABYLON.Vector3(-10, 10, -10);
            part.direction2 = new BABYLON.Vector3(10, 10, 10);
            part.emitRate = 100;
            part.blendMode = 1;
            part.start();
        }
        create_part(2);
        create_part(-2);
    }
    game.rotater.rotation.y += 0.1 * dt;
    scene.render();
}
var game = {
    load: null,
    tick: null,
    file_loaded: null,
    files_count: 2,
    files_loaded: 0,
    envtext: null,
    engine: null,
    sounds: {
        brush: null,
        punch: null,
        motor: null,
        music: null,
        up: null,
        down: null,
        enabled: true
    },
    t_x: null,
    t_y: null,
    char11: null,
    char12: null,
    char13: null,
    char21: null,
    char22: null,
    char23: null,
    brush: null,
    rotater: null,
    position: null,
    creator: null,
    checker_creator: null,
    ray_origin: null,
    ray: null,
    checker_dispose: null,
    cartel: null,
    checker: null,
    obstacle: null,
    paste: null,
    poop: null,
    win: null,
    win_coll: null,
    brush_poop: null,
    particle: null,
    t_cleaned: null,
    m_ok: null,
    TOUCHING: false,
    CURRENT: "paste",
    LEVEL: 1,
    VELOCITY: 1.5,
    PLAYING: false,
    SCORE: 0,
    dispose: function () {
        engine.stopRenderLoop(game.tick);
        scene.stopAllAnimations();
        scene.dispose();
    },
    run: function () {
        game.PLAYING = true;
        game.VELOCITY = 1 / 1.15;
        gui.avd.removeControl(gui.btn_run);
        gui.avd.removeControl(gui.howto);
        BABYLON.Engine.audioEngine.unlock();
        game.sounds.motor.play();
        game.sounds.motor.loop = true;
        if (game.sounds.music == null) {
            game.sounds.music = new BABYLON.Sound("music", "sound/lolly-by-at-limujii.mp3", scene2);
            game.sounds.music.loop = true;
            game.sounds.music.autoplay = true;
            game.sounds.music.setVolume(0.6);
        }
    }
};
var gui = {
    avd: null,
    txt: null,
    txt_score: null,
    txt_add_score: null,
    btn_run: null,
    btn_next: null,
    btn_reset: null,
    btn_sound: null,
    star_new: null,
    howto: null,
    load: function () {
        gui.avd = BABYLON.GUI.AdvancedDynamicTexture.CreateFullscreenUI("UI");
        gui.avd.idealHeight = 1024;
        var txt = new BABYLON.GUI.TextBlock("txt1", "0");
        txt.fontFamily = font_name;
        txt.fontSize = "25px";
        txt.textVerticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_TOP;
        gui.avd.addControl(txt);
        gui.txt = txt;
        var txt = new BABYLON.GUI.TextBlock("txt_score", "0");
        txt.outlineColor = "white";
        txt.outlineWidth = 10;
        txt.fontFamily = font_name;
        txt.fontSize = "100px";
        txt.top = 200;
        txt.textVerticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_TOP;
        gui.avd.addControl(txt);
        gui.txt_score = txt;
        var txt = new BABYLON.GUI.TextBlock("txt_best", "best " +
            Math.round(BABYLON.DataStorage.ReadNumber(SAVE_NAME + "RECORD", 0)));
        txt.outlineColor = "black";
        txt.outlineWidth = 5;
        txt.color = "yellow";
        txt.fontFamily = font_name;
        txt.fontSize = "32px";
        txt.top = 154;
        txt.textVerticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_TOP;
        gui.avd.addControl(txt);
        var txt = new BABYLON.GUI.TextBlock("txt_add_score", "+0");
        txt.outlineColor = "black";
        txt.outlineWidth = 5;
        txt.color = "white";
        txt.fontFamily = font_name;
        txt.fontSize = "28px";
        txt.top = 290;
        txt.alpha = 10;
        txt.textVerticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_TOP;
        gui.avd.addControl(txt);
        gui.txt_add_score = txt;
        // new record image
        var image = new BABYLON.GUI.Image("but", "images/star_new.png");
        image.width = 126 * 0.6 + "px";
        image.height = 132 * 0.6 + "px";
        image.top = "-160";
        gui.avd.addControl(image);
        gui.star_new = image;
        image.alpha = 0;
        var txt = new BABYLON.GUI.TextBlock("txt_level", "level " +
            BABYLON.DataStorage.ReadNumber(SAVE_NAME + "LEVEL", 1));
        txt.top = -12;
        txt.color = "black";
        txt.fontFamily = font_name;
        txt.fontSize = "24px";
        txt.textVerticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_BOTTOM;
        gui.avd.addControl(txt);
        //button
        var button = BABYLON.GUI.Button.CreateImageOnlyButton("but", "images/btn1.png");
        button.width = "48px";
        button.height = "48px";
        button.color = "transparent";
        button.thickness = 0;
        button.background = "transparent";
        gui.avd.addControl(button);
        button.verticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_TOP;
        button.horizontalAlignment = BABYLON.GUI.Control.HORIZONTAL_ALIGNMENT_LEFT;
        button.left = 16;
        button.top = 16;
        button.onPointerDownObservable.add(function () {
            game.dispose();
            game.load();
        });
        //button sound
        var src = "images/audio_enabled.png";
        if (!game.sounds.enabled) {
            src = "images/audio_disabled.png";
        }
        var img = new BABYLON.GUI.Image("img", "images/audio_disabled.png");
        var img2 = new BABYLON.GUI.Image("img2", "images/audio_enabled.png");
        var button = BABYLON.GUI.Button.CreateImageOnlyButton("but", src);
        gui.btn_sound = button;
        button.width = "48px";
        button.height = "48px";
        button.color = "transparent";
        button.thickness = 0;
        button.background = "transparent";
        gui.avd.addControl(button);
        button.verticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_TOP;
        button.horizontalAlignment = BABYLON.GUI.Control.HORIZONTAL_ALIGNMENT_RIGHT;
        button.left = -16;
        button.top = 16;
        button.onPointerDownObservable.add(function () {
            if (game.sounds.enabled) {
                game.sounds.enabled = false;
                gui.btn_sound.image.source = "images/audio_disabled.png";
                BABYLON.Engine.audioEngine.setGlobalVolume(0);
            }
            else {
                game.sounds.enabled = true;
                gui.btn_sound.image.source = "images/audio_enabled.png";
                BABYLON.Engine.audioEngine.setGlobalVolume(1);
            }
        });
        //button run
        var button = BABYLON.GUI.Button.CreateImageOnlyButton("but", "images/btn_run.png");
        gui.btn_run = button;
        button.width = "256px";
        button.height = "64px";
        button.color = "transparent";
        button.thickness = 0;
        button.background = "transparent";
        gui.avd.addControl(button);
        button.verticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_BOTTOM;
        button.horizontalAlignment = BABYLON.GUI.Control.HORIZONTAL_ALIGNMENT_CENTER;
        button.top = -46;
        button.onPointerUpObservable.add(function () {
            on_press_run();
            game.run();
        });
        //button next
        var button = BABYLON.GUI.Button.CreateImageOnlyButton("but", "images/btn_next.png");
        button.width = "256px";
        button.height = "64px";
        button.color = "transparent";
        button.thickness = 0;
        button.background = "transparent";
        button.verticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_BOTTOM;
        button.horizontalAlignment = BABYLON.GUI.Control.HORIZONTAL_ALIGNMENT_CENTER;
        button.top = -46;
        gui.btn_next = button;
        button.onPointerUpObservable.add(function () {
          LaggedAPI.GEvents.next();
            game.dispose();
            game.load();
        });
        //button reset
        var button = BABYLON.GUI.Button.CreateImageOnlyButton("but", "images/btn_reset.png");
        button.width = "256px";
        button.height = "64px";
        button.color = "transparent";
        button.thickness = 0;
        button.background = "transparent";
        button.verticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_BOTTOM;
        button.horizontalAlignment = BABYLON.GUI.Control.HORIZONTAL_ALIGNMENT_CENTER;
        button.top = -46;
        gui.btn_reset = button;
        button.onPointerUpObservable.add(function () {
          LaggedAPI.GEvents.next();
          console.log('reset');
            game.dispose();
            game.load();
        });
        var image = new BABYLON.GUI.Image("but", "images/howto.png");
        image.width = "220px";
        image.height = "220px";
        image.top = "240";
        gui.avd.addControl(image);
        gui.howto = image;
    }
};
var engine;
var canvas;
var scene;
var scene2;
var font_name = "font1";
var canvas2;
canvas2 = document.createElement("canvas");
var c2d = canvas2.getContext("2d");
var SAVE_NAME = "ds_2021_9_teeth_runner_3d_babylonjs_game_html5_13";
var cc = console.log;
var time_start = 0;
window.addEventListener("DOMContentLoaded", function () {
    c2d.font = "30px " + font_name;
    c2d.strokeText("text", 0, 0);
    if (window.Ammo !== undefined) {
        Ammo().then(function () {
            init();
            on_window_load();
            //time_playing = (new Date().getTime() / 1000);;
            time_start = (new Date().getTime() / 1000);
            ;
        });
    }
    else {
        init();
    }
});
function init() {
    canvas = document.getElementById("canvas");
    engine = new BABYLON.Engine(canvas);
    scene2 = new BABYLON.Scene(engine);
    game.sounds.brush = new BABYLON.Sound("BRUSH", "sound/brush.mp3", scene2);
    game.sounds.brush.setVolume(0.8);
    game.sounds.motor = new BABYLON.Sound("MOTOR", "sound/motor.mp3", scene2);
    game.sounds.motor.setVolume(0.5);
    game.sounds.punch = new BABYLON.Sound("punch", "sound/punch.mp3", scene2);
    game.sounds.up = new BABYLON.Sound("punch", "sound/up.mp3", scene2);
    game.sounds.down = new BABYLON.Sound("punch", "sound/down.mp3", scene2);
    engine.displayLoadingUI = function () { };
    window.addEventListener("resize", function () {
        engine.resize();
    });
    game.load = game_load;
    game.file_loaded = game_file_loaded;
    game.tick = game_tick;
    game.load();
}
var level_generator = {
    POOP: "poop",
    PASTE: "paste",
    CURRENT: "none",
    COUNT_CHARS_LEVEL: 25,
    CURRENT_CHAR_LEVEL: 0,
    COUNT_CHARS_GROUP: 5,
    CURRENT_CHAR_GROUP: 0,
    PLAYING: true,
    init: function () {
        var lg = level_generator;
        lg.PLAYING = true;
        level_generator.CURRENT = level_generator.PASTE;
        if (game.LEVEL < 20) {
            lg.COUNT_CHARS_LEVEL = +7 + (2 * game.LEVEL) + Math.round(Math.random() * 2);
        }
        else {
            lg.COUNT_CHARS_LEVEL = 7 + (2 * 20) + Math.round(Math.random() * 2);
        }
        lg.CURRENT = lg.PASTE;
        game.CURRENT = lg.PASTE;
        lg.COUNT_CHARS_GROUP = Math.round((Math.random() * 5) + 7);
        lg.CURRENT_CHAR_GROUP = 0;
        lg.CURRENT_CHAR_LEVEL = 0;
    },
    add: function () {
    },
    tick: function () {
        var lg = level_generator;
        game.checker_creator.setParent(null);
        if (game.creator.position.z < game.checker_creator.position.z && lg.PLAYING) {
            var newchar, type;
            if (lg.CURRENT_CHAR_GROUP < lg.COUNT_CHARS_GROUP) {
                var posible_obstacle = 0.1;
                if (game.LEVEL < 20) {
                    posible_obstacle = 0.1 + 0.015 * game.LEVEL;
                }
                else {
                    posible_obstacle = 0.1 + 0.015 * 20;
                }
                if (Math.random() > posible_obstacle) {
                    var add_change_char = Math.random();
                    var limit_ = 0.9;
                    if ((lg.CURRENT == lg.PASTE && add_change_char < limit_) ||
                        (lg.CURRENT == lg.POOP && add_change_char >= limit_)) {
                        if (game.LEVEL == 1 ||
                            (Math.random() < 0.5 && game.LEVEL < 4) ||
                            (Math.random() < 0.3333333 && game.LEVEL >= 4)) {
                            newchar = game.char11.clone("new_char", null, false);
                        }
                        else if ((game.LEVEL < 4) ||
                            (Math.random() < 0.6666666 && game.LEVEL >= 4)) {
                            newchar = game.char12.clone("new_char", null, false);
                        }
                        else {
                            newchar = game.char13.clone("new_char", null, false);
                        }
                        BABYLON.Tags.AddTagsTo(newchar, "loopeable");
                        type = "man";
                    }
                    else if ((lg.CURRENT == lg.POOP && add_change_char < limit_) ||
                        (lg.CURRENT == lg.PASTE && add_change_char >= limit_)) {
                        if (game.LEVEL == 1 ||
                            (Math.random() < 0.5 && game.LEVEL < 4) ||
                            (Math.random() < 0.333333 && game.LEVEL >= 4)) {
                            newchar = game.char21.clone("new_char", null, false);
                        }
                        else if ((game.LEVEL < 4) ||
                            (Math.random() < 0.666666 && game.LEVEL >= 4)) {
                            newchar = game.char22.clone("new_char", null, false);
                        }
                        else {
                            newchar = game.char23.clone("new_char", null, false);
                        }
                        BABYLON.Tags.AddTagsTo(newchar, "loopeable");
                        type = "ogre";
                    }
                    newchar.metadata =
                        { cleaned: 0, teeth: newchar.getChildMeshes()[0], type: type, ready: false };
                    BABYLON.Tags.AddTagsTo(newchar, "char");
                    newchar.position = game.creator.position.clone();
                    lg.CURRENT_CHAR_GROUP++;
                    lg.CURRENT_CHAR_LEVEL++;
                }
                else { //obstacle
                    var newobstacle = game.obstacle.clone("newobs", null);
                    newobstacle.position.z = game.creator.position.z;
                    BABYLON.Tags.AddTagsTo(newobstacle, "loopeable");
                    BABYLON.Tags.AddTagsTo(newobstacle, "obstacle");
                    if (Math.random() > 0.5) {
                        newobstacle.getChildMeshes()[0].position.y = -5;
                    }
                }
            }
            else if (true) {
                if (lg.CURRENT_CHAR_LEVEL < lg.COUNT_CHARS_LEVEL) {
                    if (lg.CURRENT == lg.PASTE) {
                        var newpaste = game.poop.clone("np", null);
                        BABYLON.Tags.AddTagsTo(newpaste, "loopeable");
                        newpaste.position = game.creator.position.clone();
                        lg.CURRENT = lg.POOP;
                        BABYLON.Tags.AddTagsTo(newpaste, "poop");
                    }
                    else {
                        var newpaste = game.paste.clone("np", null);
                        newpaste.visibility = 1;
                        BABYLON.Tags.AddTagsTo(newpaste, "loopeable");
                        newpaste.position = game.creator.position.clone();
                        lg.CURRENT = lg.PASTE;
                        BABYLON.Tags.AddTagsTo(newpaste, "paste");
                    }
                    lg.COUNT_CHARS_GROUP = Math.round((Math.random() * 5) + 7);
                    lg.CURRENT_CHAR_GROUP = 0;
                }
                else {
                    game.creator.position.z += 6;
                    game.win.position.z = game.creator.position.z;
                    lg.PLAYING = false;
                    ;
                }
            }
            if (lg.PLAYING) {
                game.creator.position.z += 4;
            }
        }
        game.checker_creator.setParent(game.position);
    }
};
//# sourceMappingURL=main.js.map
