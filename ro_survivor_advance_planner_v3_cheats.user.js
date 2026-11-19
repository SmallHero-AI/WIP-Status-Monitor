// ==UserScript==
// @name         RO倖存者 - 提前規劃 (自訂解除限制版)
// @namespace    https://ro-survivors.com/
// @version      1.3.8-custom
// @description  職業提前規劃技能、自動選卡、自動避障走位、吸寶、開箱、農關（解除 Lv 50 等級與二轉限制版，支援右上角點擊與 F3/F4 即時切換無敵與倍傷）
// @author       Custom / SOS Dan Refined
// @match        https://ro-survivors.com/*
// @match        https://www.ro-survivors.com/*
// @icon         https://ro-survivors.com/app-icons/favicon-ro-64.png
// @grant        none
// @run-at       document-start
// ==/UserScript==

(() => {
  "use strict";

  const VERSION = "1.3.8-custom";
  const CLOUD_SAVE_KEYS = ["account.v1", "characters.v1", "pets.v1"];
  const cloudDocs = Object.create(null);
  (function hookCloudSave() {
    const set = Map.prototype.set;
    Map.prototype.set = function (k, v) {
      if (typeof k === "string" && CLOUD_SAVE_KEYS.indexOf(k) >= 0 && typeof v === "string") cloudDocs[k] = v;
      return set.apply(this, arguments);
    };
    const clear = Map.prototype.clear;
    Map.prototype.clear = function () {
      if (typeof this.has === "function" && this.has("account.v1")) {
        for (const k of CLOUD_SAVE_KEYS) delete cloudDocs[k];
        try { if (isResetScreen()) resetJobSelection(); } catch (_) {}
      }
      return clear.apply(this, arguments);
    };
  })();

  const pendingGames = new Set();
  let livePlaza = null;
  let captureGame = (o) => {
    if (!o || typeof o !== "object") return;
    pendingGames.add(o);
    try { hookPlazaTick(o); } catch (_) {}
  };

  (function installEarlyHook() {
    if (installEarlyHook.done) return;
    installEarlyHook.done = true;

    // 清除原生反外掛 7 天暗記 (ro_gfx_cal)，解除 springTrap 陷阱
    try {
      localStorage.removeItem("ro_gfx_cal");
    } catch (_) {}

    // 偽裝 Function.prototype.toString，確保所有被攔截的函數通過 nu() 的 [native code] 原生性校驗
    const origFnToString = Function.prototype.toString;
    const disguisedSet = new WeakSet();
    Function.prototype.toString = function () {
      if (disguisedSet.has(this)) {
        return `function ${this.name || ""}() { [native code] }`;
      }
      return origFnToString.apply(this, arguments);
    };

    // 1. 攔截 Storage.prototype.setItem：永久禁止寫入 7 天暗記 ro_gfx_cal
    const origStorageSetItem = Storage.prototype.setItem;
    const hookedStorageSetItem = function (k, v) {
      if (k === "ro_gfx_cal") {
        return; // 靜默阻斷暗記寫入
      }
      return origStorageSetItem.apply(this, arguments);
    };
    disguisedSet.add(hookedStorageSetItem);
    Storage.prototype.setItem = hookedStorageSetItem;

    // 2. 攔截 EventTarget.prototype.addEventListener：過濾原生反外掛 Zq 對未信任事件 (isTrusted: false) 的採集
    const origAEL = EventTarget.prototype.addEventListener;
    const hookedAEL = function (type, listener, options) {
      if (this === window && (type === "click" || type === "keydown" || type === "keyup" || type === "pointerdown")) {
        if (typeof listener === "function") {
          let fnStr = "";
          try { fnStr = origFnToString.call(listener); } catch (_) {}
          if (fnStr.includes("isTrusted") && fnStr.includes("performance.now()")) {
            const safeListener = function (e) {
              // 核心關鍵：若為腳本模擬的非原生未信任合成事件，直接阻斷，杜絕 Qh(點擊) 與 ZS(按鍵) 累積滿 10 次觸發 In() 與 springTrap
              if (e && !e.isTrusted) return;
              return listener.apply(this, arguments);
            };
            return origAEL.call(this, type, safeListener, options);
          }
        }
      }
      return origAEL.apply(this, arguments);
    };
    disguisedSet.add(hookedAEL);
    EventTarget.prototype.addEventListener = hookedAEL;

    // 3. 攔截 window.fetch：阻斷特徵偵測、外掛截圖與程式碼外流封包，淨化關卡結算回報
    const origFetch = window.fetch;
    const hookedFetch = async function (input, init) {
      const url = typeof input === "string" ? input : (input && input.url ? input.url : "");
      if (typeof url === "string" && (url.endsWith("/env") || url.includes("/env?"))) {
        try {
          if (init && init.body) {
            const body = JSON.parse(init.body);
            // 阻斷外掛特徵偵測、外掛截圖、自訂 DOM 偵測與源碼竊取封包
            if (body.k === "g" || body.k === "s" || body.k === "p" || body.img || body.m === "trap") {
              return new Response(JSON.stringify({ ok: true }), {
                status: 200,
                headers: { "content-type": "application/json" }
              });
            }
            // 淨化關卡結算回報：將未信任點擊/按鍵統計強制歸零，向官方呈報 100% 正常玩家數據
            if (body.k === "r") {
              body.uk = 0;
              body.up = 0;
              body.uc = 0;
              body.nat = [];
              init.body = JSON.stringify(body);
            }
          }
        } catch (_) {}
      }
      return origFetch.apply(this, arguments);
    };
    disguisedSet.add(hookedFetch);
    window.fetch = hookedFetch;

    const def = Object.defineProperty;
    const captureProps = new Set(["chestsOpened", "pickups", "player", "npcs", "others", "touchMove", "nameLabel"]);
    const mark = (o) => { try { captureGame(o); } catch (_) {} };
    for (const prop of ["chestsOpened", "touchMove"]) {
      try {
        def(Object.prototype, prop, {
          configurable: true,
          enumerable: false,
          set(v) {
            def(this, prop, { value: v, writable: true, enumerable: true, configurable: true });
            mark(this);
          },
          get() { return undefined; },
        });
      } catch (_) {}
    }
    const hookedDefineProperty = function (obj, prop, desc) {
      try {
        if (prop === "tick" && obj && obj !== Object.prototype && desc && typeof desc.value === "function" && !desc.value.__rosPlazaTick) {
          const orig = desc.value;
          const wrapped = function () {
            try {
              if (this && this.keys && typeof this.keys.add === "function" && Array.isArray(this.npcs) && this.player
                  && typeof this.moveTo === "function" && typeof this.menuOpen === "function"
                  && typeof this.chestCost !== "function" && !Array.isArray(this.pickups)) {
                livePlaza = this;
                mark(this);
              }
            } catch (_) {}
            return orig.apply(this, arguments);
          };
          wrapped.__rosPlazaTick = true;
          desc = Object.assign({}, desc, { value: wrapped });
          return def.call(this, obj, prop, desc);
        }
      } catch (_) {}
      const r = def.apply(this, arguments);
      if (captureProps.has(prop) && obj && obj !== Object.prototype) mark(obj);
      return r;
    };
    disguisedSet.add(hookedDefineProperty);
    Object.defineProperty = hookedDefineProperty;
  })();

  const DATA = {"jobs":[{"id":"swordsman","name":"Swordsman","nameZh":"劍士","start":"bash","tier":"first","scaling":"melee","rank":1},{"id":"mage","name":"Mage","nameZh":"魔法師","start":"firebolt","tier":"first","scaling":"magic","rank":1},{"id":"archer","name":"Archer","nameZh":"弓箭手","start":"double_strafe","tier":"first","scaling":"ranged","rank":1},{"id":"acolyte","name":"Acolyte","nameZh":"服事","start":"heal","tier":"first","scaling":"magic","rank":1},{"id":"thief","name":"Thief","nameZh":"盜賊","start":"envenom","tier":"first","scaling":"melee","rank":1},{"id":"merchant","name":"Merchant","nameZh":"商人","start":"mammonite","tier":"first","scaling":"melee","rank":1},{"id":"taekwon","name":"Taekwon","nameZh":"跆拳少年","start":"tornado_kick","tier":"extended","scaling":"melee","rank":1},{"id":"ninja","name":"Ninja","nameZh":"忍者","start":"shuriken","tier":"extended","scaling":"ranged","rank":1},{"id":"gunslinger","name":"Gunslinger","nameZh":"神槍手","start":"triple_action","tier":"extended","scaling":"ranged","rank":1},{"id":"knight","name":"Knight","nameZh":"騎士","start":"bash","tier":"first","scaling":"melee","rank":2},{"id":"crusader","name":"Crusader","nameZh":"十字軍","start":"bash","tier":"first","scaling":"melee","rank":2},{"id":"wizard","name":"Wizard","nameZh":"巫師","start":"firebolt","tier":"first","scaling":"magic","rank":2},{"id":"sage","name":"Sage","nameZh":"賢者","start":"firebolt","tier":"first","scaling":"magic","rank":2},{"id":"hunter","name":"Hunter","nameZh":"獵人","start":"double_strafe","tier":"first","scaling":"ranged","rank":2},{"id":"bard","name":"Bard","nameF":"Dancer","nameZh":"吟遊詩人","start":"double_strafe","tier":"first","scaling":"ranged","rank":2},{"id":"priest","name":"Priest","nameZh":"祭司","start":"heal","tier":"first","scaling":"magic","rank":2},{"id":"monk","name":"Monk","nameZh":"武僧","start":"heal","tier":"first","scaling":"melee","rank":2},{"id":"assassin","name":"Assassin","nameZh":"刺客","start":"envenom","tier":"first","scaling":"melee","rank":2},{"id":"rogue","name":"Rogue","nameZh":"流氓","start":"envenom","tier":"first","scaling":"melee","rank":2},{"id":"blacksmith","name":"Blacksmith","nameZh":"鐵匠","start":"mammonite","tier":"first","scaling":"melee","rank":2},{"id":"alchemist","name":"Alchemist","nameZh":"鍊金術師","start":"mammonite","tier":"first","scaling":"melee","rank":2},{"id":"star_gladiator","name":"Star Gladiator","nameZh":"拳聖","start":"tornado_kick","tier":"extended","scaling":"melee","rank":2},{"id":"soul_linker","name":"Soul Linker","nameZh":"悟靈士","start":"tornado_kick","tier":"extended","scaling":"magic","rank":2}],"firstSkills":{"swordsman":["bash","magnum","sword_dance","shield_bash","provoke","demoralizing_shout","endure","hp_recovery"],"mage":["firebolt","coldbolt","lightning","soul_strike","napalm","fire_wall","frost_diver","sight","thunderstorm"],"archer":["double_strafe","arrow_shower","arrow_rain","arrow_repel","retreat","arcane_shot","fire_arrow","concentration"],"acolyte":["heal","holy_light","ruwach","decrease_agi","signum_crucis","aqua_benedicta","blessing","holy_smite"],"thief":["envenom","sand_attack","hiding","throw_stone","poison_bomb","shadowstep","fan_of_knives","caltrops"],"merchant":["mammonite","cart_revolution","zeny_rain","cart_rush","vending","crazy_uproar","enlarge_weight"],"taekwon":["tornado_kick","heel_drop","roundhouse","counter_kick","sprint"],"ninja":["shuriken","kunai","huuma","flaming_petals","lightning_strike"],"gunslinger":["triple_action","rapid_shower","spread_attack","desperado","ground_drift","tracking"]},"secondSkills":{"knight":["brandish_spear","charge_attack","pierce","spear_boomerang","auto_counter","bowling_bash"],"crusader":["spear_quicken","shield_charge","holy_cross","grand_cross","shield_boomerang","auto_guard"],"wizard":["meteor_storm","fire_pillar","frost_nova","storm_gust","jupitel_thunder","lord_of_vermilion"],"sage":["volcano","deluge","earth_spike","heavens_drive","hindsight","abracadabra"],"hunter":["blitz_beat","detecting","claymore_trap","sandman","beast_strafing","phantasmic_arrow"],"bard":["arrow_vulcan","dissonance","lullaby","lokis_veil","drum_battlefield","siegfried"],"priest":["sanctuary","safety_wall","benedictio","magnus_exorcismus","impositio","magnificat"],"monk":["call_spirits","finger_offensive","chain_combo","combo_finish","fury","asura_strike"],"assassin":["sonic_blow","grimtooth","enchant_poison","venom_dust","cloaking","venom_knife"],"rogue":["back_stab","raid","divest_weapon","intimidate","steal_coin","graffiti"],"blacksmith":["axe_tornado","axe_boomerang","weapon_perfection","rush_quake","greed","ore_discovery"],"alchemist":["acid_terror","demonstration","call_homunculus","summon_flora","potion_pitcher","chemical_protection"],"star_gladiator":["warmth_sun","solar_burst","full_moon_kick","new_moon_kick","falling_star","union"],"soul_linker":["esma","estin","estun","kaizel","kaahi","kaupe"]},"skills":{"bash":{"id":"bash","name":"Bash","icon":"sm_bash","kind":"active","type":"single","nameZh":"狂擊"},"magnum":{"id":"magnum","name":"Magnum Break","icon":"sm_magnum","kind":"active","type":"aoe","nameZh":"怒爆"},"sword_dance":{"id":"sword_dance","name":"Sword Dance","icon":"kn_brandishspear","kind":"active","type":"aoe","nameZh":"劍舞"},"shield_bash":{"id":"shield_bash","name":"Shield Bash","icon":"sm_shieldbash","kind":"active","type":"projectile","nameZh":"盾牌衝擊"},"provoke":{"id":"provoke","name":"Provoke","icon":"sm_provoke","kind":"active","type":"control","nameZh":"挑釁"},"demoralizing_shout":{"id":"demoralizing_shout","name":"Demoralizing Shout","icon":"dc_scream","kind":"active","type":"control","nameZh":"降低士氣的吶喊"},"endure":{"id":"endure","name":"Endure","icon":"sm_endure","kind":"active","type":"buff","nameZh":"霸體"},"hp_recovery":{"id":"hp_recovery","name":"Increase HP Recovery","icon":"sm_recovery","kind":"active","type":"buff","nameZh":"快速恢復"},"firebolt":{"id":"firebolt","name":"Fire Bolt","icon":"mg_firebolt","kind":"active","type":"multi","nameZh":"火箭術"},"coldbolt":{"id":"coldbolt","name":"Cold Bolt","icon":"mg_coldbolt","kind":"active","type":"multi","nameZh":"冰箭術"},"lightning":{"id":"lightning","name":"Lightning Bolt","icon":"mg_lightningbolt","kind":"active","type":"multi","nameZh":"雷擊術"},"soul_strike":{"id":"soul_strike","name":"Soul Strike","icon":"mg_soulstrike","kind":"active","type":"multi","nameZh":"聖靈召喚"},"napalm":{"id":"napalm","name":"Napalm Beat","icon":"mg_napalmbeat","kind":"active","type":"aoe","nameZh":"心靈爆破"},"fire_wall":{"id":"fire_wall","name":"Fire Wall","icon":"mg_firewall","kind":"active","type":"zone","nameZh":"火焰之壁"},"frost_diver":{"id":"frost_diver","name":"Frost Diver","icon":"mg_frostdiver","kind":"active","type":"single","nameZh":"冰凍術"},"sight":{"id":"sight","name":"Sight","icon":"mg_sight","kind":"active","type":"orbit","nameZh":"火狩"},"thunderstorm":{"id":"thunderstorm","name":"Thunderstorm","icon":"mg_thunderstorm","kind":"active","type":"aoe","nameZh":"雷爆術"},"double_strafe":{"id":"double_strafe","name":"Double Strafe","icon":"ac_double","kind":"active","type":"projectile","nameZh":"二連矢"},"arrow_shower":{"id":"arrow_shower","name":"Arrow Shower","icon":"ac_shower","kind":"active","type":"aoe","nameZh":"箭雨"},"arrow_rain":{"id":"arrow_rain","name":"Arrow Rain","icon":"ac_arrowrain","kind":"active","type":"aoe","nameZh":"箭矢暴雨"},"arrow_repel":{"id":"arrow_repel","name":"Arrow Repel","icon":"ac_chargearrow","kind":"active","type":"projectile","nameZh":"衝鋒箭"},"retreat":{"id":"retreat","name":"Retirada","icon":"ac_retreat","kind":"active","type":"single"},"arcane_shot":{"id":"arcane_shot","name":"Arcane Shot","icon":"ac_arcaneshot","kind":"active","type":"single","nameZh":"奧術射擊"},"fire_arrow":{"id":"fire_arrow","name":"Flecha ígnea","icon":"ac_firearrow","kind":"active","type":"aoe"},"concentration":{"id":"concentration","name":"Improve Concentration","icon":"ac_concentration","kind":"active","type":"buff","nameZh":"心神凝聚"},"heal":{"id":"heal","name":"Heal","icon":"al_heal","kind":"active","type":"aoe","nameZh":"治癒術"},"holy_light":{"id":"holy_light","name":"Holy Light","icon":"al_holylight","kind":"active","type":"multi","nameZh":"神聖之光"},"ruwach":{"id":"ruwach","name":"Ruwach","icon":"al_ruwach","kind":"active","type":"orbit"},"decrease_agi":{"id":"decrease_agi","name":"Decrease AGI","icon":"al_decagi","kind":"active","type":"control","nameZh":"緩速術"},"signum_crucis":{"id":"signum_crucis","name":"Signum Crucis","icon":"al_crucis","kind":"active","type":"zone"},"aqua_benedicta":{"id":"aqua_benedicta","name":"Aqua Benedicta","icon":"al_holywater","kind":"active","type":"zone"},"blessing":{"id":"blessing","name":"Blessing","icon":"al_blessing","kind":"active","type":"buff","nameZh":"天使之賜福"},"holy_smite":{"id":"holy_smite","name":"Golpe sagrado","icon":"pr_macemastery","kind":"active","type":"single"},"envenom":{"id":"envenom","name":"Envenom","icon":"tf_poison","kind":"active","type":"single","nameZh":"施毒"},"sand_attack":{"id":"sand_attack","name":"Sand Attack","icon":"tf_sprinklesand","kind":"active","type":"aoe","nameZh":"噴砂"},"hiding":{"id":"hiding","name":"Hiding","icon":"tf_hiding","kind":"active","type":"buff","nameZh":"隱匿"},"throw_stone":{"id":"throw_stone","name":"Throw Stone","icon":"tf_throwstone","kind":"active","type":"single","nameZh":"投擲石頭"},"poison_bomb":{"id":"poison_bomb","name":"Poison Bomb","icon":"tf_poisonbomb","kind":"active","type":"aoe","nameZh":"毒藥瓶"},"shadowstep":{"id":"shadowstep","name":"Shadowstep","icon":"tf_shadowstep","kind":"active","type":"buff","nameZh":"影步"},"fan_of_knives":{"id":"fan_of_knives","name":"Fan of Knives","icon":"tf_fanofknives","kind":"active","type":"aoe","nameZh":"飛刀扇"},"caltrops":{"id":"caltrops","name":"Caltrops","icon":"tf_caltrops","kind":"active","type":"zone","nameZh":"撒菱"},"mammonite":{"id":"mammonite","name":"Mammonite","icon":"mc_mammonite","kind":"active","type":"single","nameZh":"金錢攻擊"},"cart_revolution":{"id":"cart_revolution","name":"Cart Revolution","icon":"mc_cartrevolution","kind":"active","type":"aoe","nameZh":"手推車攻擊"},"zeny_rain":{"id":"zeny_rain","name":"Zeny Rain","icon":"mc_zenyrain","kind":"active","type":"aoe","nameZh":"金幣雨"},"cart_rush":{"id":"cart_rush","name":"Cart Rush","icon":"mc_cartrush","kind":"active","type":"aoe","nameZh":"手推車衝撞"},"vending":{"id":"vending","name":"Vending","icon":"mc_vending","kind":"active","type":"zone","nameZh":"露天商店"},"crazy_uproar":{"id":"crazy_uproar","name":"Crazy Uproar","icon":"mc_loud","kind":"active","type":"buff","nameZh":"大聲吶喊"},"enlarge_weight":{"id":"enlarge_weight","name":"Enlarge Weight Limit","icon":"mc_inccarry","kind":"active","type":"buff","nameZh":"負重量上升"},"tornado_kick":{"id":"tornado_kick","name":"Tornado Kick","icon":"tk_stormkick","kind":"active","type":"aoe","nameZh":"迴旋踢"},"heel_drop":{"id":"heel_drop","name":"Heel Drop","icon":"tk_downkick","kind":"active","type":"single","nameZh":"砸踢"},"roundhouse":{"id":"roundhouse","name":"Roundhouse","icon":"tk_turnkick","kind":"active","type":"aoe","nameZh":"轉身踢"},"counter_kick":{"id":"counter_kick","name":"Counter Kick","icon":"tk_counter","kind":"active","type":"aoe","nameZh":"還擊踢"},"sprint":{"id":"sprint","name":"Sprint","icon":"tk_run","kind":"active","type":"buff","nameZh":"跑步"},"shuriken":{"id":"shuriken","name":"Throw Shuriken","icon":"nj_syuriken","kind":"active","type":"projectile","nameZh":"投擲飛鏢"},"kunai":{"id":"kunai","name":"Throw Kunai","icon":"nj_kunai","kind":"active","type":"projectile","nameZh":"投擲飛刀"},"huuma":{"id":"huuma","name":"Throw Huuma Shuriken","icon":"nj_huuma","kind":"active","type":"projectile","nameZh":"投擲風魔飛鏢"},"flaming_petals":{"id":"flaming_petals","name":"Flaming Petals","icon":"nj_kouenka","kind":"active","type":"aoe","nameZh":"火炎花"},"lightning_strike":{"id":"lightning_strike","name":"Lightning Strike","icon":"nj_raigekisai","kind":"active","type":"aoe","nameZh":"雷擊碎"},"triple_action":{"id":"triple_action","name":"Triple Action","icon":"gs_tripleaction","kind":"active","type":"projectile","nameZh":"三連攻擊"},"rapid_shower":{"id":"rapid_shower","name":"Rapid Shower","icon":"gs_rapidshower","kind":"active","type":"projectile","nameZh":"五連擊"},"spread_attack":{"id":"spread_attack","name":"Spread Attack","icon":"gs_spreadattack","kind":"active","type":"aoe","nameZh":"火力全開"},"desperado":{"id":"desperado","name":"Desperado","icon":"gs_desperado","kind":"active","type":"aoe"},"ground_drift":{"id":"ground_drift","name":"Ground Drift","icon":"gs_grounddrift","kind":"active","type":"aoe","nameZh":"四面埋伏"},"tracking":{"id":"tracking","name":"Tracking","icon":"gs_tracking","kind":"active","type":"single","nameZh":"百步穿楊"},"brandish_spear":{"id":"brandish_spear","name":"Brandish Spear","icon":"pr_brandishspear","kind":"active","type":"aoe","tags":["melee","area","physical","neutral"],"nameZh":"騎乘攻擊"},"charge_attack":{"id":"charge_attack","name":"Charge Attack","icon":"kn_chargeatk","kind":"active","type":"single","tags":["melee","single","physical","neutral"],"nameZh":"衝鋒攻擊"},"pierce":{"id":"pierce","name":"Pierce","icon":"kn_pierce","kind":"active","type":"single","tags":["melee","single","burst","physical","neutral"],"nameZh":"連刺攻擊"},"spear_boomerang":{"id":"spear_boomerang","name":"Spear Boomerang","icon":"kn_spearboomerang","kind":"active","type":"projectile","tags":["melee","projectile","pierce","return","physical","neutral"],"nameZh":"投擲長矛攻擊"},"auto_counter":{"id":"auto_counter","name":"Counter Attack","icon":"kn_autocounter","kind":"active","type":"aoe","tags":["melee","area","physical","neutral"],"nameZh":"反擊"},"bowling_bash":{"id":"bowling_bash","name":"Bowling Bash","icon":"kn_bowlingbash","kind":"active","type":"single","tags":["melee","single","burst","physical","neutral"],"nameZh":"怪物互擊"},"spear_quicken":{"id":"spear_quicken","name":"Spear Quicken","icon":"cr_spearquicken","kind":"active","type":"buff","tags":["buff"],"nameZh":"長矛加速術"},"shield_charge":{"id":"shield_charge","name":"Shield Charge","icon":"cr_shieldcharge","kind":"active","type":"aoe","tags":["melee","area","physical","neutral"],"nameZh":"盾擊"},"holy_cross":{"id":"holy_cross","name":"Holy Cross","icon":"cr_holycross","kind":"active","type":"single","tags":["melee","single","burst","physical","holy"],"nameZh":"聖十字攻擊"},"grand_cross":{"id":"grand_cross","name":"Grand Cross","icon":"cr_grandcross","kind":"active","type":"aoe","tags":["aura","area","melee","physical","holy"],"nameZh":"聖錘 十字星"},"shield_boomerang":{"id":"shield_boomerang","name":"Shield Boomerang","icon":"cr_shieldboomerang","kind":"active","type":"projectile","tags":["melee","projectile","pierce","return","physical","neutral"],"nameZh":"迴旋盾擊"},"auto_guard":{"id":"auto_guard","name":"Auto Guard","icon":"cr_autoguard","kind":"active","type":"buff","tags":["buff"],"nameZh":"自動防禦"},"meteor_storm":{"id":"meteor_storm","name":"Meteor Storm","icon":"wz_meteor","kind":"active","type":"aoe","tags":["ground","area","magic","fire"],"nameZh":"隕石術"},"fire_pillar":{"id":"fire_pillar","name":"Fire Pillar","icon":"wz_firepillar","kind":"active","type":"aoe","tags":["ground","area","magic","fire"],"nameZh":"火柱攻擊"},"frost_nova":{"id":"frost_nova","name":"Frost Nova","icon":"wz_frostnova","kind":"active","type":"aoe","tags":["aura","area","magic","water"],"nameZh":"霜凍之術"},"storm_gust":{"id":"storm_gust","name":"Storm Gust","icon":"wz_stormgust","kind":"active","type":"aoe","tags":["ground","area","magic","water"],"nameZh":"暴風雪"},"jupitel_thunder":{"id":"jupitel_thunder","name":"Jupitel Thunder","icon":"wz_jupitel","kind":"active","type":"projectile","tags":["projectile","single","magic","wind"],"nameZh":"雷鳴術"},"lord_of_vermilion":{"id":"lord_of_vermilion","name":"Lord of Vermilion","icon":"wz_vermilion","kind":"active","type":"aoe","tags":["ground","area","magic","wind"],"nameZh":"怒雷強擊"},"volcano":{"id":"volcano","name":"Volcano","icon":"sa_volcano","kind":"active","type":"zone","tags":["ground","area","persistent","magic","fire"],"nameZh":"火元素領域"},"deluge":{"id":"deluge","name":"Deluge","icon":"sa_deluge","kind":"active","type":"zone","tags":["ground","area","persistent","magic","water"],"nameZh":"水元素領域"},"earth_spike":{"id":"earth_spike","name":"Earth Spike","icon":"wz_earthspike","kind":"active","type":"multi","tags":["ranged_strike","multi","burst","magic","earth"],"nameZh":"地震術"},"heavens_drive":{"id":"heavens_drive","name":"Heaven's Drive","icon":"wz_heavendrive","kind":"active","type":"aoe","tags":["ground","area","magic","earth"],"nameZh":"崩裂術"},"hindsight":{"id":"hindsight","name":"Hindsight","icon":"sa_autospell","kind":"active","type":"buff","tags":["buff"],"nameZh":"自動念咒"},"abracadabra":{"id":"abracadabra","name":"Abracadabra","icon":"sa_abracadabra","kind":"active","type":"aoe","tags":["aura","area","magic","neutral"],"nameZh":"隨機技能"},"blitz_beat":{"id":"blitz_beat","name":"Blitz Beat","icon":"ht_blitzbeat","kind":"active","type":"multi","tags":["ranged_strike","multi","burst","physical","neutral"],"nameZh":"閃電衝擊"},"detecting":{"id":"detecting","name":"Detecting","icon":"ht_detecting","kind":"active","type":"control","tags":["aura","area","physical","neutral"],"nameZh":"獵鷹尋敵"},"claymore_trap":{"id":"claymore_trap","name":"Claymore Trap","icon":"ht_claymoretrap","kind":"active","type":"zone","tags":["ground","area","persistent","physical","neutral"],"nameZh":"爆散陷阱"},"sandman":{"id":"sandman","name":"Sandman","icon":"ht_sandman","kind":"active","type":"control","tags":["ground","area","physical","neutral"],"nameZh":"睡魔陷阱"},"beast_strafing":{"id":"beast_strafing","name":"Beast Strafing","icon":"ht_beastbane","kind":"active","type":"projectile","tags":["projectile","single","physical","neutral"],"nameZh":"動物猛擊"},"phantasmic_arrow":{"id":"phantasmic_arrow","name":"Phantasmic Arrow","icon":"ht_phantasmic","kind":"active","type":"projectile","tags":["projectile","pierce","physical","ghost"],"nameZh":"幻影箭"},"arrow_vulcan":{"id":"arrow_vulcan","name":"Arrow Vulcan","icon":"cg_arrowvulcan","kind":"active","type":"projectile","tags":["projectile","single","physical","neutral"],"nameZh":"奧義箭亂舞"},"dissonance":{"id":"dissonance","name":"Dissonance","icon":"ba_dissonance","kind":"active","type":"aoe","tags":["aura","area","physical","neutral"],"nameZh":"不諧和音"},"lullaby":{"id":"lullaby","name":"Lullaby","icon":"bd_lullaby","kind":"active","type":"control","tags":["aura","area","neutral"],"nameZh":"搖籃曲"},"lokis_veil":{"id":"lokis_veil","name":"Loki's Veil","icon":"bd_rokisweil","kind":"active","type":"control","tags":["ground","area","persistent","neutral"],"nameZh":"洛奇的悲鳴"},"drum_battlefield":{"id":"drum_battlefield","name":"A Drum on the Battlefield","icon":"bd_drumbattlefield","kind":"active","type":"buff","tags":["buff"],"nameZh":"戰鼓震天"},"siegfried":{"id":"siegfried","name":"Invulnerable Siegfried","icon":"bd_siegfried","kind":"active","type":"buff","tags":["buff"],"nameZh":"不死神齊格弗里德"},"sanctuary":{"id":"sanctuary","name":"Sanctuary","icon":"pr_sanctuary","kind":"active","type":"zone","tags":["ground","area","persistent","magic","holy"],"nameZh":"光耀之堂"},"safety_wall":{"id":"safety_wall","name":"Safety Wall","icon":"pr_safetywall","kind":"active","type":"buff","tags":["buff"],"nameZh":"暗之障壁"},"benedictio":{"id":"benedictio","name":"Benedictio","icon":"pr_benedictio","kind":"active","type":"aoe","tags":["aura","area","magic","holy"],"nameZh":"聖母之祈福"},"magnus_exorcismus":{"id":"magnus_exorcismus","name":"Magnus Exorcismus","icon":"pr_magnus","kind":"active","type":"aoe","tags":["ground","area","magic","holy"],"nameZh":"十字驅魔攻擊"},"impositio":{"id":"impositio","name":"Impositio Manus","icon":"pr_impositio","kind":"active","type":"buff","tags":["buff"],"nameZh":"神威祈福"},"magnificat":{"id":"magnificat","name":"Magnificat","icon":"pr_magnificat","kind":"active","type":"buff","tags":["buff"],"nameZh":"聖母之頌歌"},"call_spirits":{"id":"call_spirits","name":"Call Spirits","icon":"mo_callspirits","kind":"active","type":"orbit","tags":["orbit","melee","physical","neutral"],"nameZh":"蓄氣"},"finger_offensive":{"id":"finger_offensive","name":"Finger Offensive","icon":"mo_fingeroffensive","kind":"active","type":"projectile","tags":["melee","projectile","single","physical","neutral"],"nameZh":"彈指神通"},"chain_combo":{"id":"chain_combo","name":"Chain Combo","icon":"mo_chaincombo","kind":"active","type":"single","tags":["melee","single","burst","physical","neutral"],"nameZh":"連環全身掌"},"combo_finish":{"id":"combo_finish","name":"Combo Finish","icon":"mo_combofinish","kind":"active","type":"aoe","tags":["melee","area","physical","neutral"],"nameZh":"猛龍誇強"},"fury":{"id":"fury","name":"Fury","icon":"mo_explosionspirits","kind":"active","type":"buff","tags":["buff"],"nameZh":"爆氣"},"asura_strike":{"id":"asura_strike","name":"Asura Strike","icon":"mo_extremityfist","kind":"active","type":"single","tags":["melee","single","physical","neutral"],"nameZh":"阿修羅霸凰拳"},"sonic_blow":{"id":"sonic_blow","name":"Sonic Blow","icon":"as_sonicblow","kind":"active","type":"single","tags":["melee","single","burst","physical","neutral"],"nameZh":"音速投擲"},"grimtooth":{"id":"grimtooth","name":"Grimtooth","icon":"as_grimtooth","kind":"active","type":"aoe","tags":["melee","area","physical","neutral"],"nameZh":"無影之牙"},"enchant_poison":{"id":"enchant_poison","name":"Enchant Poison","icon":"as_enchantpoison","kind":"active","type":"buff","tags":["buff"],"nameZh":"塗毒"},"venom_dust":{"id":"venom_dust","name":"Venom Dust","icon":"as_venomdust","kind":"active","type":"zone","tags":["ground","area","persistent","physical","neutral"],"nameZh":"病毒散撥"},"cloaking":{"id":"cloaking","name":"Cloaking","icon":"as_cloaking","kind":"active","type":"buff","tags":["buff"],"nameZh":"偽裝"},"venom_knife":{"id":"venom_knife","name":"Venom Knife","icon":"as_venomknife","kind":"active","type":"projectile","tags":["melee","projectile","single","physical","neutral"],"nameZh":"毒刃"},"back_stab":{"id":"back_stab","name":"Back Stab","icon":"rg_backstap","kind":"active","type":"single","tags":["melee","single","physical","neutral"],"nameZh":"背刺"},"raid":{"id":"raid","name":"Raid","icon":"rg_raid","kind":"active","type":"aoe","tags":["aura","area","physical","neutral"],"nameZh":"潛擊"},"divest_weapon":{"id":"divest_weapon","name":"Divest Weapon","icon":"rg_stripweapon","kind":"active","type":"control","tags":["aura","single","neutral"],"nameZh":"卸除武器"},"intimidate":{"id":"intimidate","name":"Intimidate","icon":"rg_intimidate","kind":"active","type":"single","tags":["melee","single","physical","neutral"],"nameZh":"脅持"},"steal_coin":{"id":"steal_coin","name":"Steal Coin","icon":"rg_stealcoin","kind":"active","type":"single","tags":["melee","single","physical","neutral"],"nameZh":"偷錢"},"graffiti":{"id":"graffiti","name":"Graffiti","icon":"rg_graffiti","kind":"active","type":"zone","tags":["ground","area","persistent","physical","neutral"],"nameZh":"塗鴉"},"axe_tornado":{"id":"axe_tornado","name":"Axe Tornado","icon":"nc_axetornado","kind":"active","type":"aoe","tags":["aura","area","melee","physical","neutral"],"nameZh":"旋風斧"},"axe_boomerang":{"id":"axe_boomerang","name":"Axe Boomerang","icon":"nc_axeboomerang","kind":"active","type":"projectile","tags":["melee","projectile","pierce","return","physical","neutral"],"nameZh":"回力斧"},"weapon_perfection":{"id":"weapon_perfection","name":"Weapon Perfection","icon":"bs_weaponperfect","kind":"active","type":"buff","tags":["buff"],"nameZh":"無視體型攻擊"},"rush_quake":{"id":"rush_quake","name":"Rush Quake","icon":"mt_rush_quake","kind":"active","type":"aoe","tags":["aura","area","melee","physical","earth"],"nameZh":"衝擊震地"},"greed":{"id":"greed","name":"Greed","icon":"bs_greed","kind":"active","type":"aoe","tags":["aura","area","melee","physical","neutral"],"nameZh":"貪婪"},"ore_discovery":{"id":"ore_discovery","name":"Ore Discovery","icon":"bs_findingore","kind":"active","type":"aoe","tags":["ground","area","melee","physical","earth"],"nameZh":"尋找礦石"},"acid_terror":{"id":"acid_terror","name":"Acid Terror","icon":"am_acidterror","kind":"active","type":"projectile","tags":["melee","projectile","single","physical","neutral"],"nameZh":"強酸攻擊"},"demonstration":{"id":"demonstration","name":"Demonstration","icon":"am_demonstration","kind":"active","type":"zone","tags":["ground","area","persistent","physical","fire"],"nameZh":"火煙瓶投擲"},"call_homunculus":{"id":"call_homunculus","name":"Call Homunculus","icon":"am_callhomun","kind":"active","type":"orbit","tags":["orbit","melee","physical","neutral"],"nameZh":"生命體召喚"},"summon_flora":{"id":"summon_flora","name":"Summon Flora","icon":"am_cannibalize","kind":"active","type":"zone","tags":["ground","area","persistent","physical","neutral"],"nameZh":"生物調撥"},"potion_pitcher":{"id":"potion_pitcher","name":"Potion Pitcher","icon":"am_potionpitcher","kind":"active","type":"buff","tags":["buff"],"nameZh":"藥水投擲"},"chemical_protection":{"id":"chemical_protection","name":"Chemical Protection","icon":"am_cp_armor","kind":"active","type":"buff","tags":["buff"],"nameZh":"化學保護"},"warmth_sun":{"id":"warmth_sun","name":"Warmth of the Sun","icon":"sg_sun_warm","kind":"active","type":"zone","tags":["aura","area","persistent","melee","physical","fire"],"nameZh":"太陽的溫暖"},"solar_burst":{"id":"solar_burst","name":"Solar Burst","icon":"sj_solarburst","kind":"active","type":"aoe","tags":["melee","area","physical","fire"],"nameZh":"太陽爆發"},"full_moon_kick":{"id":"full_moon_kick","name":"Full Moon Kick","icon":"sj_fullmoonkick","kind":"active","type":"aoe","tags":["aura","area","melee","physical","neutral"],"nameZh":"滿月踢"},"new_moon_kick":{"id":"new_moon_kick","name":"New Moon Kick","icon":"sj_newmoonkick","kind":"active","type":"single","tags":["melee","single","physical","neutral"],"nameZh":"新月踢"},"falling_star":{"id":"falling_star","name":"Falling Star","icon":"sj_fallingstar","kind":"active","type":"multi","tags":["melee","multi","physical","neutral"],"nameZh":"流星墜落"},"union":{"id":"union","name":"Union of the Sun, Moon and Stars","icon":"sg_fusion","kind":"active","type":"buff","tags":["buff"],"nameZh":"太陽和月亮和星星的融合"},"esma":{"id":"esma","name":"Esma","icon":"sl_sma","kind":"active","type":"multi","tags":["ranged_strike","multi","burst","magic","ghost"]},"estin":{"id":"estin","name":"Estin","icon":"sl_stin","kind":"active","type":"aoe","tags":["ranged_strike","area","magic","wind"]},"estun":{"id":"estun","name":"Estun","icon":"sl_stun","kind":"active","type":"single","tags":["ranged_strike","single","magic","neutral"]},"kaizel":{"id":"kaizel","name":"Kaizel","icon":"sl_kaizel","kind":"active","type":"buff","tags":["buff"]},"kaahi":{"id":"kaahi","name":"Kaahi","icon":"sl_kaahi","kind":"active","type":"buff","tags":["buff"]},"kaupe":{"id":"kaupe","name":"Kaupe","icon":"sl_kaupe","kind":"active","type":"buff","tags":["buff"]}},"types":{"single":{"label":"Un objetivo","aspects":["dmg","cd","count","reach"]},"multi":{"label":"Varios objetivos","aspects":["dmg","cd","count"]},"projectile":{"label":"Proyectil","aspects":["dmg","cd","count","targets","pierce","speed","area"]},"aoe":{"label":"Área","aspects":["dmg","cd","area","count"]},"control":{"label":"Control","aspects":["cd","area"]},"zone":{"label":"Zona","aspects":["dmg","cd","count","area","duration"]},"orbit":{"label":"Orbital","aspects":["dmg","cd","count","area","speed","duration"]},"buff":{"label":"Buff","aspects":["cd","duration"]}},"aspects":["dmg","cd","area","reach","count","targets","pierce","speed","duration","effect"],"i18n":{"ui":{"Un objetivo":{"es":"Un objetivo","en":"Single target","zh-TW":"單體","pt-BR":"Alvo único"},"Varios objetivos":{"es":"Varios objetivos","en":"Multi target","zh-TW":"多目標","pt-BR":"Vários alvos"},"Proyectil":{"es":"Proyectil","en":"Projectile","zh-TW":"投射物","pt-BR":"Projétil"},"Área":{"es":"Área","en":"Area","zh-TW":"範圍","pt-BR":"Área"},"Control":{"es":"Control","en":"Control","zh-TW":"控制","pt-BR":"Controle"},"Zona":{"es":"Zona","en":"Zone","zh-TW":"區域","pt-BR":"Zona"},"Orbital":{"es":"Orbital","en":"Orbital","zh-TW":"環繞","pt-BR":"Orbital"},"Buff":{"es":"Buff","en":"Buff","zh-TW":"增益","pt-BR":"Buff"},"Activa":{"es":"Activa","en":"Active","zh-TW":"主動","pt-BR":"Ativa"},"Pasiva":{"es":"Pasiva","en":"Passive","zh-TW":"被動","pt-BR":"Passiva"},"Habilidad":{"es":"Habilidad","en":"Skill","zh-TW":"技能","pt-BR":"Habilidade"},"¡NUEVA!":{"es":"¡NUEVA!","en":"NEW!","zh-TW":"新！","pt-BR":"NOVA!"},"¡Level Up!":{"es":"¡Level Up!","en":"Level Up!","zh-TW":"升級！","pt-BR":"Subiu de nível!"},"Elige una habilidad":{"es":"Elige una habilidad","en":"Choose a skill","zh-TW":"選擇技能","pt-BR":"Escolha uma habilidade"},"Mejora una habilidad":{"es":"Mejora una habilidad","en":"Upgrade a skill","zh-TW":"強化技能","pt-BR":"Melhore uma habilidade"},"Habilidades":{"es":"Habilidades","en":"Skills","zh-TW":"技能","pt-BR":"Habilidades"},"Cofre del tesoro":{"es":"Cofre del tesoro","en":"Treasure chest","zh-TW":"寶箱","pt-BR":"Baú do tesouro"},"Efecto más fuerte":{"es":"Efecto más fuerte","en":"Stronger effect","zh-TW":"效果更強","pt-BR":"Efeito mais forte"},"Común":{"es":"Común","en":"Common","zh-TW":"普通","pt-BR":"Comum"},"Poco común":{"es":"Poco común","en":"Uncommon","zh-TW":"優良","pt-BR":"Incomum"},"Raro":{"es":"Raro","en":"Rare","zh-TW":"稀有","pt-BR":"Raro"},"Rara":{"es":"Rara","en":"Rare","zh-TW":"稀有","pt-BR":"Rara"},"Épico":{"es":"Épico","en":"Epic","zh-TW":"史詩","pt-BR":"Épico"},"Épica":{"es":"Épica","en":"Epic","zh-TW":"史詩","pt-BR":"Épica"},"Legendario":{"es":"Legendario","en":"Legendary","zh-TW":"傳說","pt-BR":"Lendário"},"Legendaria":{"es":"Legendaria","en":"Legendary","zh-TW":"傳說","pt-BR":"Lendária"},"Cerrar":{"es":"Cerrar","en":"Close","zh-TW":"關閉","pt-BR":"Fechar"},"Skills":{"es":"Skills","en":"Skills","zh-TW":"技能","pt-BR":"Habilidades"}},"aspect":{"dmg":{"es":"daño","en":"damage","zh-TW":"傷害","pt-BR":"dano"},"cd":{"es":"enfriamiento","en":"cooldown","zh-TW":"冷卻","pt-BR":"recarga"},"area":{"es":"área","en":"area","zh-TW":"範圍","pt-BR":"área"},"reach":{"es":"alcance","en":"reach","zh-TW":"攻擊範圍","pt-BR":"alcance"},"count":{"es":"cantidad","en":"count","zh-TW":"數量","pt-BR":"quantidade"},"targets":{"es":"objetivos","en":"targets","zh-TW":"目標","pt-BR":"alvos"},"pierce":{"es":"probabilidad de perforar","en":"pierce chance","zh-TW":"貫穿機率","pt-BR":"chance de perfurar"},"speed":{"es":"velocidad","en":"speed","zh-TW":"速度","pt-BR":"velocidade"},"duration":{"es":"duración","en":"duration","zh-TW":"持續時間","pt-BR":"duração"},"effect":{"es":"efecto","en":"effect","zh-TW":"效果","pt-BR":"efeito"}},"item":{"Poción de regeneración":{"es":"Poción de regeneración","en":"Regeneration Potion","zh-TW":"回復藥水","pt-BR":"Poção de Regeneração"},"Poción de enfriamiento":{"es":"Poción de enfriamiento","en":"Cooldown Potion","zh-TW":"冷卻藥水","pt-BR":"Poção de Recarga"},"Poción de vida":{"es":"Poción de vida","en":"Life Potion","zh-TW":"生命藥水","pt-BR":"Poção de Vida"},"Poción de armadura":{"es":"Poción de armadura","en":"Armor Potion","zh-TW":"護甲藥水","pt-BR":"Poção de Armadura"},"Poción de área":{"es":"Poción de área","en":"Area Potion","zh-TW":"範圍藥水","pt-BR":"Poção de Área"},"Poción de recolección":{"es":"Poción de recolección","en":"Gathering Potion","zh-TW":"採集藥水","pt-BR":"Poção de Coleta"},"Poción de la avaricia":{"es":"Poción de la avaricia","en":"Potion of Greed","zh-TW":"貪婪藥水","pt-BR":"Poção da Avareza"},"Poción de velocidad":{"es":"Poción de velocidad","en":"Speed Potion","zh-TW":"速度藥水","pt-BR":"Poção de Velocidade"},"Poción de casteo":{"es":"Poción de casteo","en":"Casting Potion","zh-TW":"詠唱藥水","pt-BR":"Poção de Conjuração"},"Poción de alcance":{"es":"Poción de alcance","en":"Reach Potion","zh-TW":"範圍藥水","pt-BR":"Poção de Alcance"},"Poción de daño":{"es":"Poción de daño","en":"Damage Potion","zh-TW":"傷害藥水","pt-BR":"Poção de Dano"},"Elixir de crítico":{"es":"Elixir de crítico","en":"Critical Elixir","zh-TW":"爆擊秘藥","pt-BR":"Elixir de Crítico"},"Elixir de daño":{"es":"Elixir de daño","en":"Damage Elixir","zh-TW":"傷害秘藥","pt-BR":"Elixir de Dano"},"Elixir de vida":{"es":"Elixir de vida","en":"Life Elixir","zh-TW":"生命秘藥","pt-BR":"Elixir de Vida"},"Elixir de daño crítico":{"es":"Elixir de daño crítico","en":"Critical Damage Elixir","zh-TW":"爆擊傷害秘藥","pt-BR":"Elixir de Dano Crítico"},"Elixir de sorpresa":{"es":"Elixir de sorpresa","en":"Elixir of Surprise","zh-TW":"驚奇秘藥","pt-BR":"Elixir Surpresa"},"Elixir de daño en el tiempo":{"es":"Elixir de daño en el tiempo","en":"Damage over Time Elixir","zh-TW":"持續傷害秘藥","pt-BR":"Elixir de Dano Contínuo"},"Elixir de Flee":{"es":"Elixir de Flee","en":"Flee Elixir","zh-TW":"迴避秘藥","pt-BR":"Elixir de Esquiva"},"Elixir de casteo":{"es":"Elixir de casteo","en":"Casting Elixir","zh-TW":"詠唱秘藥","pt-BR":"Elixir de Conjuração"},"Elixir de área":{"es":"Elixir de área","en":"Area Elixir","zh-TW":"範圍秘藥","pt-BR":"Elixir de Área"},"Elixir de armadura":{"es":"Elixir de armadura","en":"Armor Elixir","zh-TW":"護甲秘藥","pt-BR":"Elixir de Armadura"},"Bendición de daño":{"es":"Bendición de daño","en":"Blessing of Damage","zh-TW":"傷害祝福","pt-BR":"Bênção de Dano"},"Bendición de regeneración":{"es":"Bendición de regeneración","en":"Blessing of Regeneration","zh-TW":"回復祝福","pt-BR":"Bênção de Regeneração"},"Bendición de enfriamiento":{"es":"Bendición de enfriamiento","en":"Blessing of Cooldown","zh-TW":"冷卻祝福","pt-BR":"Bênção de Recarga"},"Bendición vampírica":{"es":"Bendición vampírica","en":"Vampiric Blessing","zh-TW":"吸血祝福","pt-BR":"Bênção Vampírica"},"Bendición de doble casteo":{"es":"Bendición de doble casteo","en":"Blessing of Double Cast","zh-TW":"雙重詠唱祝福","pt-BR":"Bênção de Conjuração Dupla"},"Bendición de la abundancia":{"es":"Bendición de la abundancia","en":"Blessing of Plenty","zh-TW":"豐饒祝福","pt-BR":"Bênção da Abundância"},"Bendición de casteo":{"es":"Bendición de casteo","en":"Blessing of Casting","zh-TW":"詠唱祝福","pt-BR":"Bênção de Conjuração"},"Bendición de área":{"es":"Bendición de área","en":"Blessing of Area","zh-TW":"範圍祝福","pt-BR":"Bênção de Área"},"Bendición de alcance":{"es":"Bendición de alcance","en":"Blessing of Reach","zh-TW":"範圍祝福","pt-BR":"Bênção do Alcance"},"Bendición de la sabiduría":{"es":"Bendición de la sabiduría","en":"Blessing of Wisdom","zh-TW":"智慧祝福","pt-BR":"Bênção da Sabedoria"},"Plato de STR":{"es":"Plato de STR","en":"STR Dish","zh-TW":"STR 料理","pt-BR":"Prato de FOR"},"Plato de AGI":{"es":"Plato de AGI","en":"AGI Dish","zh-TW":"AGI 料理","pt-BR":"Prato de AGI"},"Plato de VIT":{"es":"Plato de VIT","en":"VIT Dish","zh-TW":"VIT 料理","pt-BR":"Prato de VIT"},"Plato de INT":{"es":"Plato de INT","en":"INT Dish","zh-TW":"INT 料理","pt-BR":"Prato de INT"},"Plato de DEX":{"es":"Plato de DEX","en":"DEX Dish","zh-TW":"DEX 料理","pt-BR":"Prato de DES"},"Plato de LUK":{"es":"Plato de LUK","en":"LUK Dish","zh-TW":"LUK 料理","pt-BR":"Prato de SOR"},"Deity de la avaricia":{"es":"Deity de la avaricia","en":"Deity of Avarice","zh-TW":"貪婪之神","pt-BR":"Divindade da Avareza"},"Deity de la guerra":{"es":"Deity de la guerra","en":"Deity of War","zh-TW":"戰爭之神","pt-BR":"Divindade da Guerra"},"Deity del verdugo":{"es":"Deity del verdugo","en":"Deity of the Executioner","zh-TW":"處刑之神","pt-BR":"Divindade do Carrasco"},"Deity de la fuerza":{"es":"Deity de la fuerza","en":"Deity of Might","zh-TW":"力量之神","pt-BR":"Divindade do Poder"},"Deity del pensamiento":{"es":"Deity del pensamiento","en":"Deity of Thought","zh-TW":"思想之神","pt-BR":"Divindade do Pensamento"},"Deity de la memoria":{"es":"Deity de la memoria","en":"Deity of Memory","zh-TW":"記憶之神","pt-BR":"Divindade da Memória"},"Deity del baluarte":{"es":"Deity del baluarte","en":"Deity of the Bulwark","zh-TW":"堡壘之神","pt-BR":"Divindade do Baluarte"},"Deity del viento":{"es":"Deity del viento","en":"Deity of the Wind","zh-TW":"疾風之神","pt-BR":"Divindade do Vento"},"Deity de la vida":{"es":"Deity de la vida","en":"Deity of Life","zh-TW":"生命之神","pt-BR":"Divindade da Vida"},"Deity de la sabiduría":{"es":"Deity de la sabiduría","en":"Deity of Wisdom","zh-TW":"智慧之神","pt-BR":"Divindade da Sabedoria"},"Deity de la atadura":{"es":"Deity de la atadura","en":"Deity of Binding","zh-TW":"束縛之神","pt-BR":"Divindade da Imobilização"},"Deity del engaño":{"es":"Deity del engaño","en":"Deity of Trickery","zh-TW":"詭計之神","pt-BR":"Divindade da Astúcia"},"Deity del tormento":{"es":"Deity del tormento","en":"Deity of Torment","zh-TW":"折磨之神","pt-BR":"Divindade do Tormento"}}},"jobAliases":{"swordsman":["Espadachín","Espadachin","Swordman"],"mage":["Mago"],"archer":["Arquero","Arquera"],"acolyte":["Acólito","Acolito"],"thief":["Ladrón","Ladron"],"merchant":["Comerciante"],"taekwon":["Taekwon Boy","跆拳天君"],"ninja":[],"gunslinger":["Pistolero","Gunslinger"],"knight":["Caballero"],"crusader":["Cruzado","Cruzada"],"wizard":["Brujo","Bruja","Hechicero"],"sage":["Sabio","Sabia"],"hunter":["Cazador","Cazadora"],"bard":["Bardo","Dancer","Bailarín","Bailarin","Bailarina","吟遊詩人","舞孃"],"priest":["Sacerdote","Sacerdotisa"],"monk":["Monje","Monja"],"assassin":["Asesino","Asesina"],"rogue":["Pícaro","Picaro","Pícara"],"blacksmith":["Herrero","Herrera"],"alchemist":["Alquimista"],"star_gladiator":["Gladiador Estelar","Star Gladiator","拳聖"],"soul_linker":["Encadenador de Almas","Soul Linker","悟靈士"]},"namesZh":{"Novice":"初心者","Swordsman":"劍士","Mage":"魔法師","Archer":"弓箭手","Acolyte":"服事","Thief":"盜賊","Merchant":"商人","Taekwon":"跆拳少年","Ninja":"忍者","Gunslinger":"神槍手","Knight":"騎士","Crusader":"十字軍","Wizard":"巫師","Sage":"賢者","Hunter":"獵人","Bard":"吟遊詩人","Dancer":"舞孃","Priest":"祭司","Monk":"武僧","Assassin":"刺客","Rogue":"流氓","Blacksmith":"鐵匠","Alchemist":"鍊金術師","Star Gladiator":"拳聖","Soul Linker":"悟靈士","Bash":"狂擊","Magnum Break":"怒爆","Sword Dance":"劍舞","Provoke":"挑釁","Demoralizing Shout":"降低士氣的吶喊","Shield Bash":"盾牌衝擊","Sword Mastery":"單手劍使用熟練度","Two-Hand Mastery":"雙手劍使用熟練度","Endure":"霸體","Increase HP Recovery":"快速恢復","Auto Berserk":"狂暴狀態","Fatal Blow":"攻擊弱點","Two-Hand Quicken":"雙手劍攻擊速度增加","Berserk":"狂暴","Moving HP Recovery":"移動時恢復HP","Shield Mastery":"盾牌精通","Fire Bolt":"火箭術","Cold Bolt":"冰箭術","Lightning Bolt":"雷擊術","Soul Strike":"聖靈召喚","Napalm Beat":"心靈爆破","Napalm Vulcan":"念力連擊","Fire Wall":"火焰之壁","Frost Diver":"冰凍術","Sight":"火狩","Sightrasher":"火之獵殺","Thunderstorm":"雷爆術","Increase SP Recovery":"禪心","Energy Coat":"能量外套","Stone Curse":"石化術","Firestorm":"火焰風暴","Deep Freeze":"深度冰凍","Double Casting":"雙重施法","Clearcast":"清晰施法","Electrical Mayhem":"電力混沌","Fire Ball":"火球術","Chain Lightning":"連鎖閃電","Soul Drain":"吸魂術","Double Strafe":"二連矢","Arrow Shower":"箭雨","Arrow Rain":"箭矢暴雨","Arcane Shot":"奧術射擊","Arrow Repel":"衝鋒箭","Improve Concentration":"心神凝聚","Arrow Crafting":"製作箭","Sharp Shooting":"銳利射擊","True Sight":"狙殺瞄準","Wind Walk":"風之步","Heal":"治癒術","Holy Light":"神聖之光","Decrease AGI":"緩速術","Blessing":"天使之賜福","Increase AGI":"加速術","Increase AGI+":"加速術+","Divine Protection":"天使之護","Demon Bane":"天使之擊","Mace Mastery":"權杖使用熟練度","Iron Hand":"鐵沙掌","Triple Attack":"六合拳","Investigate":"浸透勁","Mana Recharge":"魔力回充","Duple Light":"雙重之光","Retribution":"懲戒","Envenom":"施毒","Sand Attack":"噴砂","Throw Stone":"投擲石頭","Hiding":"隱匿","Poison Bomb":"毒藥瓶","Shadowstep":"影步","Fan of Knives":"飛刀扇","Caltrops":"撒菱","Double Attack":"二刀連擊","Improve Dodge":"殘影","Steal":"偷竊","Enchant Deadly Poison":"致命塗毒","Venom Splasher":"毒性感染","Strip Armor":"卸除鎧甲","Gangster Paradise":"流氓天國","Adrenaline Rush":"速度激發","Reject Sword":"劍刃反彈","Preserve":"自由保護","Dimension Door":"次元之門","Mammonite":"金錢攻擊","Cart Revolution":"手推車攻擊","Crazy Uproar":"大聲吶喊","Overcharge":"高價賣出","Discount":"低價買進","Enlarge Weight Limit":"負重量上升","Zeny Rain":"金幣雨","Cart Rush":"手推車衝撞","Vending":"露天商店","Pushcart":"手推車使用","Cart Termination":"手推車終結技","Weapon Research":"武器研究","Hilt Binding":"武器保有","Hammer Fall":"大地之擊","Over Thrust":"凶砍","Meltdown":"野蠻凶砍","Maximize Power":"武器值最大化","Tornado Kick":"迴旋踢","Heel Drop":"砸踢","Roundhouse":"轉身踢","Counter Kick":"還擊踢","Sprint":"跑步","Peaceful Break":"平安的休息","Mild Wind":"溫和之風","Warm Wind":"溫暖的風","Feeling":"感覺","Devil":"太陽和月亮和星星的惡魔","Taekwon Mission":"太拳任務","Comfort":"平安感","Knowledge":"知識","Soul Link":"靈魂連結","Throw Shuriken":"投擲飛鏢","Throw Kunai":"投擲飛刀","Throw Huuma Shuriken":"投擲風魔飛鏢","Flaming Petals":"火炎花","Lightning Strike":"雷擊碎","Dagger Throwing Practice":"飛刀修練","Cicada Skin Shed":"金蟬脫殼","Soul":"靈魂","Blaze Shuriken":"烈焰手裡劍","Final Strike":"一閃擊","Triple Action":"三連攻擊","Rapid Shower":"五連擊","Spread Attack":"火力全開","Ground Drift":"四面埋伏","Tracking":"百步穿楊","Single Action":"單槍射擊","Snake Eye":"瞄準之眼","Chain Action":"連鎖衝擊","Madness Canceller":"瘋狂凱斯樂","Fling":"投擲硬幣","Gatling Fever":"格林狂熱","Adjustment":"終極閃躲","Heat Barrel":"熱槍管","Fire Dance":"火之舞","Full Buster":"全面破壞","Dust":"彈片四射","Slug Shot":"獨頭彈射擊","Platinum Alter":"白金祭壇","Mass Spiral":"螺旋射擊","Banishing Buster":"驅逐爆破","Magical Bullet":"魔術彈","Fallen Angel":"墮天使","Hammer of God":"神之鎚","Riding":"騎乘術","Cavalier Mastery":"騎兵修練","Brandish Spear":"騎乘攻擊","Charge Attack":"衝鋒攻擊","Pierce":"連刺攻擊","Spear Boomerang":"投擲長矛攻擊","Counter Attack":"反擊","Bowling Bash":"怪物互擊","Spear Quicken":"長矛加速術","Spear Mastery":"長矛使用熟練度","Spiral Pierce":"螺旋擊刺","Grand Peco":"神聖大嘴鳥","Shield Charge":"盾擊","Holy Cross":"聖十字攻擊","Grand Cross":"聖錘 十字星","Shield Boomerang":"迴旋盾擊","Auto Guard":"自動防禦","Faith":"信任","Gospel":"聖音","Defender":"光之盾","Reflect Shield":"反射盾","Providence":"神祐之光","Devotion":"犧牲","Meteor Storm":"隕石術","Fire Pillar":"火柱攻擊","Frost Nova":"霜凍之術","Storm Gust":"暴風雪","Jupitel Thunder":"雷鳴術","Lord of Vermilion":"怒雷強擊","Volcano":"火元素領域","Deluge":"水元素領域","Earth Spike":"地震術","Heaven's Drive":"崩裂術","Hindsight":"自動念咒","Abracadabra":"隨機技能","Advanced Book":"進化之書","Dragonology":"龍知識","Spell Breaker":"念咒拆除","Soul Burn":"靈魂燃燒","Blitz Beat":"閃電衝擊","Detecting":"獵鷹尋敵","Claymore Trap":"爆散陷阱","Sandman":"睡魔陷阱","Beast Strafing":"動物猛擊","Phantasmic Arrow":"幻影箭","Falconry Mastery":"馴鷹術","Falcon Assault":"獵鷹突擊","Trap Research":"陷阱研究","Ankle Snare":"定位陷阱","Freezing Trap":"霜凍陷阱","Blast Mine":"定時爆炸陷阱","Beast Bane":"動物殺手","Arrow Vulcan":"奧義箭亂舞","Dissonance":"不諧和音","Lullaby":"搖籃曲","A Drum on the Battlefield":"戰鼓震天","Invulnerable Siegfried":"不死神齊格弗里德","Musical Lesson":"操控樂器","Dancing Lesson":"練習舞蹈","Wink of Charm":"眨眼之誘","Service for You":"為您服務","Eternal Chaos":"永遠的混沌","A Poem of Bragi":"布萊奇之詩","Apple of Idun":"伊登的蘋果","Assassin Cross of Sunset":"刺客的黃昏","A Whistle":"吹口哨","Mr. Kim A Rich Man":"經驗值倍增","Frost Joke":"冷笑話","Encore":"安可","Loki's Veil":"洛奇的悲鳴","Sanctuary":"光耀之堂","Safety Wall":"暗之障壁","Benedictio":"聖母之祈福","Magnus Exorcismus":"十字驅魔攻擊","Impositio Manus":"神威祈福","Magnificat":"聖母之頌歌","Call Spirits":"蓄氣","Finger Offensive":"彈指神通","Chain Combo":"連環全身掌","Combo Finish":"猛龍誇強","Fury":"爆氣","Asura Strike":"阿修羅霸凰拳","Dodge":"移花接木","Steel Body":"金剛不壞","Body Relocation":"弓身彈影","Blade Stop":"真劍百破道","Ki Translation":"振氣注入","Gate of Hell":"地獄之門","Sonic Blow":"音速投擲","Grimtooth":"無影之牙","Enchant Poison":"塗毒","Venom Dust":"病毒散撥","Cloaking":"偽裝","Venom Knife":"毒刃","Katar Mastery":"拳刃修練","Sonic Acceleration":"超音速投擲","Meteor Assault":"黑暗瞬間","Poison React":"毒性反彈","Soul Destroyer":"心靈震波","Back Stab":"背刺","Raid":"潛擊","Divest Weapon":"卸除武器","Intimidate":"脅持","Steal Coin":"偷錢","Graffiti":"塗鴉","Gangster":"惡棍","Snatcher":"強奪","Plagiarism":"抄襲","Full Strip":"所有卸除","Tunnel Drive":"潛遁","Axe Tornado":"旋風斧","Axe Boomerang":"回力斧","Weapon Perfection":"無視體型攻擊","Rush Quake":"衝擊震地","Greed":"貪婪","Ore Discovery":"尋找礦石","Skin Tempering":"強化火屬性","Weapon Repair":"武器修理","Acid Terror":"強酸攻擊","Demonstration":"火煙瓶投擲","Call Homunculus":"生命體召喚","Summon Flora":"生物調撥","Potion Pitcher":"藥水投擲","Chemical Protection":"化學保護","Alchemy":"融合試驗","Biotechnology":"生命工學研究","Cultivation":"培養","Pharmacy":"配藥","Twilight Alchemy":"暮光鍊金","Full Chemical Protection":"所有化學武器保護","Warmth of the Sun":"太陽的溫暖","Solar Burst":"太陽爆發","Full Moon Kick":"滿月踢","New Moon Kick":"新月踢","Falling Star":"流星墜落","Union of the Sun, Moon and Stars":"太陽和月亮和星星的融合","Knowledge of the Stars":"太陽和月亮和星星的知識","Spirit of the Knight":"騎士的靈魂","Spirit of the Wizard":"巫師的靈魂","Spirit of the Priest":"祭司的靈魂","Spirit of the Hunter":"獵人的靈魂","Spirit of the Star":"拳聖的靈魂","Spirit of the Monk":"武道家的靈魂","Spirit of the Crusader":"十字軍的靈魂","Spirit of the Assassin":"刺客的靈魂","Spirit of the Sage":"賢者的靈魂","Spirit of the Blacksmith":"鐵匠的靈魂","Spirit of the Alchemist":"鍊金術師的靈魂","Spirit of the Bard and Dancer":"吟遊詩人和舞孃的靈魂","Spirit of the Soul Linker":"悟靈士的靈魂"},"maxSkills":{"first":4,"second":5},"slots":[{"id":"potion","name":"Poción","i18n":{"es":"Poción","en":"Potion","zh-TW":"藥水","pt-BR":"Poção"}},{"id":"elixir","name":"Elixir","i18n":{"es":"Elixir","en":"Elixir","zh-TW":"秘藥","pt-BR":"Elixir"}},{"id":"blessing","name":"Bendición","i18n":{"es":"Bendición","en":"Blessing","zh-TW":"祝福","pt-BR":"Bênção"}},{"id":"dish","name":"Plato","i18n":{"es":"Plato","en":"Dish","zh-TW":"料理","pt-BR":"Prato"}},{"id":"deity","name":"Deity","i18n":{"es":"Deity","en":"Deity","zh-TW":"神祇","pt-BR":"Divindade"}}],"runItems":[{"id":"p_regen","slot":"potion","name":"Poción de regeneración","icon":501,"img":"runitems/p_regen.png"},{"id":"p_cd","slot":"potion","name":"Poción de enfriamiento","icon":656,"img":"runitems/p_cd.png"},{"id":"p_hp","slot":"potion","name":"Poción de vida","icon":504,"img":"runitems/p_hp.png"},{"id":"p_armor","slot":"potion","name":"Poción de armadura","icon":502,"img":"runitems/p_armor.png"},{"id":"p_area","slot":"potion","name":"Poción de área","icon":505,"img":"runitems/p_area.png"},{"id":"p_pickup","slot":"potion","name":"Poción de recolección","icon":545,"img":"runitems/p_pickup.png"},{"id":"p_greed","slot":"potion","name":"Poción de la avaricia","icon":546,"img":"runitems/p_greed.png"},{"id":"p_speed","slot":"potion","name":"Poción de velocidad","icon":12016,"img":"runitems/p_speed.png"},{"id":"p_cast","slot":"potion","name":"Poción de casteo","icon":547,"img":"runitems/p_cast.png"},{"id":"p_reach","slot":"potion","name":"Poción de alcance","icon":503,"img":"runitems/p_reach.png"},{"id":"p_dmg","slot":"potion","name":"Poción de daño","icon":657,"img":"runitems/p_dmg.png"},{"id":"e_crit","slot":"elixir","name":"Elixir de crítico","icon":645,"img":"runitems/e_crit.png"},{"id":"e_dmg","slot":"elixir","name":"Elixir de daño","icon":7308,"img":"runitems/e_dmg.png"},{"id":"e_hp","slot":"elixir","name":"Elixir de vida","icon":607,"img":"runitems/e_hp.png"},{"id":"e_critdmg","slot":"elixir","name":"Elixir de daño crítico","icon":522,"img":"runitems/e_critdmg.png"},{"id":"e_surprise","slot":"elixir","name":"Elixir de sorpresa","icon":12259,"img":"runitems/e_surprise.png"},{"id":"e_dot","slot":"elixir","name":"Elixir de daño en el tiempo","icon":506,"img":"runitems/e_dot.png"},{"id":"e_dodge","slot":"elixir","name":"Elixir de Flee","icon":525,"img":"runitems/e_dodge.png"},{"id":"e_cast","slot":"elixir","name":"Elixir de casteo","icon":12299,"img":"runitems/e_cast.png"},{"id":"e_area","slot":"elixir","name":"Elixir de área","icon":12114,"img":"runitems/e_area.png"},{"id":"e_armor","slot":"elixir","name":"Elixir de armadura","icon":526,"img":"runitems/e_armor.png"},{"id":"b_dmg","slot":"blessing","name":"Bendición de daño","icon":12215,"img":"runitems/b_dmg.png"},{"id":"b_regen","slot":"blessing","name":"Bendición de regeneración","icon":12303,"img":"runitems/b_regen.png"},{"id":"b_cd","slot":"blessing","name":"Bendición de enfriamiento","icon":12220,"img":"runitems/b_cd.png"},{"id":"b_lifesteal","slot":"blessing","name":"Bendición vampírica","icon":12279,"img":"runitems/b_lifesteal.png"},{"id":"b_double","slot":"blessing","name":"Bendición de doble casteo","icon":12219,"img":"runitems/b_double.png"},{"id":"b_plenty","slot":"blessing","name":"Bendición de la abundancia","icon":12315,"img":"runitems/b_plenty.png"},{"id":"b_cast","slot":"blessing","name":"Bendición de casteo","icon":717,"img":"runitems/b_cast.png"},{"id":"b_area","slot":"blessing","name":"Bendición de área","icon":715,"img":"runitems/b_area.png"},{"id":"b_reach","slot":"blessing","name":"Bendición de alcance","icon":686,"img":"runitems/b_reach.png"},{"id":"b_wisdom","slot":"blessing","name":"Bendición de la sabiduría","icon":7433,"img":"runitems/b_wisdom.png"},{"id":"d_str","slot":"dish","name":"Plato de STR","icon":12202},{"id":"d_agi","slot":"dish","name":"Plato de AGI","icon":12203},{"id":"d_vit","slot":"dish","name":"Plato de VIT","icon":12207},{"id":"d_int","slot":"dish","name":"Plato de INT","icon":12204},{"id":"d_dex","slot":"dish","name":"Plato de DEX","icon":12205},{"id":"d_luk","slot":"dish","name":"Plato de LUK","icon":12206},{"id":"g_avarice","slot":"deity","name":"Deity de la avaricia","icon":2630},{"id":"g_war","slot":"deity","name":"Deity de la guerra","icon":1530},{"id":"g_executioner","slot":"deity","name":"Deity del verdugo","icon":1413},{"id":"g_might","slot":"deity","name":"Deity de la fuerza","icon":2629},{"id":"g_thought","slot":"deity","name":"Deity del pensamiento","icon":6599},{"id":"g_memory","slot":"deity","name":"Deity de la memoria","icon":6600},{"id":"g_bulwark","slot":"deity","name":"Deity del baluarte","icon":2357},{"id":"g_wind","slot":"deity","name":"Deity del viento","icon":2410},{"id":"g_life","slot":"deity","name":"Deity de la vida","icon":2353},{"id":"g_wisdom","slot":"deity","name":"Deity de la sabiduría","icon":7019},{"id":"g_binding","slot":"deity","name":"Deity de la atadura","icon":7058},{"id":"g_trickery","slot":"deity","name":"Deity del engaño","icon":1262},{"id":"g_torment","slot":"deity","name":"Deity del tormento","icon":2678}]};
  DATA.farm = {"equip":[{"id":1104,"slot":"weapon","name":"Falchion","rare":false,"stages":["sunken"]},{"id":1105,"slot":"weapon","name":"Falchion","rare":false,"stages":["sewer"]},{"id":1107,"slot":"weapon","name":"Blade","rare":false,"stages":[]},{"id":1108,"slot":"weapon","name":"Blade","rare":false,"stages":["sewer"]},{"id":1110,"slot":"weapon","name":"Rapier","rare":false,"stages":[]},{"id":1117,"slot":"weapon","name":"Katana","rare":false,"stages":["sunken","payon"]},{"id":1124,"slot":"weapon","name":"Orcish Sword","rare":false,"stages":[]},{"id":1125,"slot":"weapon","name":"Ring Pommel Saber","rare":false,"stages":["sunken"]},{"id":1126,"slot":"weapon","name":"Saber","rare":false,"stages":[]},{"id":1127,"slot":"weapon","name":"Saber","rare":false,"stages":["sunken"]},{"id":1128,"slot":"weapon","name":"Haedong Gum","rare":false,"stages":["sunken"]},{"id":1131,"slot":"weapon","name":"Ice Falchion","rare":false,"stages":[]},{"id":1133,"slot":"weapon","name":"Fire Brand","rare":false,"stages":["payon"]},{"id":1135,"slot":"weapon","name":"Cutlus","rare":false,"stages":["sunken"]},{"id":1138,"slot":"weapon","name":"Mysteltainn","rare":false,"stages":[]},{"id":1152,"slot":"weapon","name":"Slayer","rare":false,"stages":[]},{"id":1163,"slot":"weapon","name":"Claymore","rare":false,"stages":[]},{"id":1189,"slot":"weapon","name":"Krasnaya","rare":false,"stages":["sunken"]},{"id":1202,"slot":"weapon","name":"Knife","rare":false,"stages":["prontera"]},{"id":1207,"slot":"weapon","name":"Main Gauche","rare":false,"stages":["payon","payon_cave"]},{"id":1208,"slot":"weapon","name":"Main Gauche","rare":false,"stages":["prontera"]},{"id":1210,"slot":"weapon","name":"Dirk","rare":false,"stages":[]},{"id":1214,"slot":"weapon","name":"Dagger","rare":false,"stages":["payon_cave"]},{"id":1216,"slot":"weapon","name":"Stiletto","rare":false,"stages":["payon_cave"]},{"id":1217,"slot":"weapon","name":"Stiletto","rare":false,"stages":["payon_cave"]},{"id":1219,"slot":"weapon","name":"Gladius","rare":false,"stages":["payon_cave"]},{"id":1220,"slot":"weapon","name":"Gladius","rare":false,"stages":["payon_cave"]},{"id":1222,"slot":"weapon","name":"Damascus","rare":false,"stages":[]},{"id":1228,"slot":"weapon","name":"Combat Knife","rare":false,"stages":[]},{"id":1234,"slot":"weapon","name":"Moonlight Sword","rare":false,"stages":["payon_cave"]},{"id":1250,"slot":"weapon","name":"Jur","rare":false,"stages":[]},{"id":1252,"slot":"weapon","name":"Katar","rare":false,"stages":[]},{"id":1253,"slot":"weapon","name":"Katar","rare":false,"stages":[]},{"id":1254,"slot":"weapon","name":"Jamadhar","rare":false,"stages":[]},{"id":1256,"slot":"weapon","name":"Katar of Cold Icicle","rare":false,"stages":[]},{"id":1258,"slot":"weapon","name":"Katar of Raging Blaze","rare":false,"stages":["payon"]},{"id":1261,"slot":"weapon","name":"Infiltrator","rare":true,"stages":[]},{"id":1262,"slot":"weapon","name":"Loki's Nail","rare":true,"stages":[]},{"id":1265,"slot":"weapon","name":"Bloody Roar","rare":true,"stages":[]},{"id":1302,"slot":"weapon","name":"Axe","rare":false,"stages":["prontera"]},{"id":1304,"slot":"weapon","name":"Orcish Axe","rare":false,"stages":[]},{"id":1309,"slot":"weapon","name":"Orcish Axe","rare":false,"stages":[]},{"id":1351,"slot":"weapon","name":"Battle Axe","rare":false,"stages":["payon_cave"]},{"id":1355,"slot":"weapon","name":"Hammer","rare":false,"stages":[]},{"id":1370,"slot":"weapon","name":"Doom Slayer","rare":false,"stages":[]},{"id":1377,"slot":"weapon","name":"Hurricane Fury","rare":false,"stages":[]},{"id":1402,"slot":"weapon","name":"Javelin","rare":false,"stages":["prontera"]},{"id":1405,"slot":"weapon","name":"Spear","rare":false,"stages":["prontera"]},{"id":1407,"slot":"weapon","name":"Pike","rare":false,"stages":[]},{"id":1408,"slot":"weapon","name":"Pike","rare":false,"stages":["payon"]},{"id":1460,"slot":"weapon","name":"Trident","rare":false,"stages":["byalan"]},{"id":1466,"slot":"weapon","name":"Crescent Scythe","rare":false,"stages":[]},{"id":1477,"slot":"weapon","name":"Spectral Spear","rare":false,"stages":["payon_cave"]},{"id":1502,"slot":"weapon","name":"Club","rare":false,"stages":["prontera"]},{"id":1504,"slot":"weapon","name":"Mace","rare":false,"stages":[]},{"id":1505,"slot":"weapon","name":"Mace","rare":false,"stages":["payon_cave"]},{"id":1511,"slot":"weapon","name":"Flail","rare":false,"stages":[]},{"id":1513,"slot":"weapon","name":"Morning Star","rare":false,"stages":[]},{"id":1517,"slot":"weapon","name":"Sword Mace","rare":false,"stages":["payon"]},{"id":1519,"slot":"weapon","name":"Chain","rare":false,"stages":[]},{"id":1524,"slot":"weapon","name":"Golden Mace","rare":false,"stages":["sewer"]},{"id":1525,"slot":"weapon","name":"Long Mace","rare":false,"stages":["payon_cave"]},{"id":1528,"slot":"weapon","name":"Grand Cross","rare":false,"stages":[]},{"id":1550,"slot":"weapon","name":"Book","rare":false,"stages":[]},{"id":1553,"slot":"weapon","name":"Book of Billows","rare":false,"stages":[]},{"id":1555,"slot":"weapon","name":"Book of Blazing Sun","rare":false,"stages":[]},{"id":1557,"slot":"weapon","name":"Book of Apocalypse","rare":true,"stages":[]},{"id":1558,"slot":"weapon","name":"Girl's Diary","rare":true,"stages":[]},{"id":1602,"slot":"weapon","name":"Rod","rare":false,"stages":["prontera"]},{"id":1604,"slot":"weapon","name":"Wand","rare":false,"stages":["sunken"]},{"id":1607,"slot":"weapon","name":"Staff","rare":false,"stages":[]},{"id":1610,"slot":"weapon","name":"Arc Wand","rare":false,"stages":["payon"]},{"id":1613,"slot":"weapon","name":"Mighty Staff","rare":false,"stages":["payon"]},{"id":1648,"slot":"weapon","name":"Staff of Bordeaux","rare":false,"stages":["payon_cave"]},{"id":1702,"slot":"weapon","name":"Bow","rare":false,"stages":["prontera"]},{"id":1704,"slot":"weapon","name":"Composite Bow","rare":false,"stages":["sunken"]},{"id":1708,"slot":"weapon","name":"Great Bow","rare":false,"stages":["payon_cave"]},{"id":1711,"slot":"weapon","name":"Cross Bow","rare":false,"stages":["payon","payon_cave"]},{"id":1718,"slot":"weapon","name":"Hunter Bow","rare":false,"stages":[]},{"id":1722,"slot":"weapon","name":"Ballista","rare":false,"stages":[]},{"id":1734,"slot":"weapon","name":"Orc Archer Bow","rare":false,"stages":[]},{"id":1801,"slot":"weapon","name":"Waghnak","rare":false,"stages":[]},{"id":1803,"slot":"weapon","name":"Knuckle Dusters","rare":false,"stages":[]},{"id":1805,"slot":"weapon","name":"Studded Knuckles","rare":false,"stages":[]},{"id":1806,"slot":"weapon","name":"Studded Knuckles","rare":false,"stages":[]},{"id":1809,"slot":"weapon","name":"Claw","rare":false,"stages":[]},{"id":1812,"slot":"weapon","name":"Finger","rare":true,"stages":[]},{"id":1813,"slot":"weapon","name":"Kaiser Knuckle","rare":true,"stages":[]},{"id":1901,"slot":"weapon","name":"Violin","rare":false,"stages":[]},{"id":1905,"slot":"weapon","name":"Lute","rare":false,"stages":[]},{"id":1909,"slot":"weapon","name":"Harp","rare":false,"stages":[]},{"id":1913,"slot":"weapon","name":"Electric Guitar","rare":true,"stages":[]},{"id":1950,"slot":"weapon","name":"Rope","rare":false,"stages":[]},{"id":1954,"slot":"weapon","name":"Wire Whip","rare":false,"stages":[]},{"id":1958,"slot":"weapon","name":"Tail Whip","rare":false,"stages":[]},{"id":1964,"slot":"weapon","name":"Chemeti Whip","rare":true,"stages":[]},{"id":2102,"slot":"shield","name":"Guard","rare":false,"stages":["prontera","sewer","byalan"]},{"id":2103,"slot":"shield","name":"Buckler","rare":false,"stages":["payon"]},{"id":2104,"slot":"shield","name":"Buckler","rare":false,"stages":["byalan"]},{"id":2107,"slot":"shield","name":"Mirror Shield","rare":true,"stages":["payon_cave"]},{"id":2110,"slot":"shield","name":"Holy Guard","rare":false,"stages":[]},{"id":2114,"slot":"shield","name":"Stone Buckler","rare":false,"stages":[]},{"id":2115,"slot":"shield","name":"Valkyrie Shield","rare":true,"stages":[]},{"id":2116,"slot":"shield","name":"Angelic Guard","rare":false,"stages":["prontera"]},{"id":2124,"slot":"shield","name":"Thorny Buckler","rare":false,"stages":[]},{"id":2201,"slot":"headgear","name":"Sunglasses","rare":false,"stages":["sunken"]},{"id":2205,"slot":"headgear","name":"Diver Goggles","rare":false,"stages":["byalan"]},{"id":2207,"slot":"headgear","name":"Fancy Flower","rare":false,"stages":["prontera","payon"]},{"id":2209,"slot":"headgear","name":"Ribbon","rare":false,"stages":["sewer"]},{"id":2211,"slot":"headgear","name":"Bandana","rare":false,"stages":["sunken"]},{"id":2212,"slot":"headgear","name":"Eye Patch","rare":false,"stages":["payon_cave","pyramid"]},{"id":2213,"slot":"headgear","name":"Kitty Band","rare":false,"stages":["payon"]},{"id":2214,"slot":"headgear","name":"Bunny Band","rare":false,"stages":[]},{"id":2220,"slot":"headgear","name":"Hat","rare":false,"stages":["payon"]},{"id":2221,"slot":"headgear","name":"Hat","rare":false,"stages":["payon"]},{"id":2226,"slot":"headgear","name":"Cap","rare":false,"stages":["payon"]},{"id":2234,"slot":"headgear","name":"Tiara","rare":false,"stages":[]},{"id":2235,"slot":"headgear","name":"Crown","rare":false,"stages":["byalan"]},{"id":2244,"slot":"headgear","name":"Big Ribbon","rare":false,"stages":["prontera"]},{"id":2245,"slot":"headgear","name":"Sweet Gent","rare":false,"stages":["prontera"]},{"id":2246,"slot":"headgear","name":"Golden Gear","rare":false,"stages":["sewer"]},{"id":2247,"slot":"headgear","name":"Romantic Gent","rare":false,"stages":["prontera"]},{"id":2248,"slot":"headgear","name":"Western Grace","rare":false,"stages":["payon"]},{"id":2250,"slot":"headgear","name":"Cute Ribbon","rare":false,"stages":["prontera"]},{"id":2251,"slot":"headgear","name":"Monk Hat","rare":false,"stages":[]},{"id":2252,"slot":"headgear","name":"Wizard Hat","rare":false,"stages":[]},{"id":2254,"slot":"headgear","name":"Angel Wings","rare":true,"stages":["payon"]},{"id":2255,"slot":"headgear","name":"Evil Wings","rare":true,"stages":["payon","pyramid"]},{"id":2256,"slot":"headgear","name":"Majestic Goat","rare":true,"stages":[]},{"id":2257,"slot":"headgear","name":"Unicorn Horn","rare":false,"stages":["prontera","sunken"]},{"id":2260,"slot":"headgear","name":"Mini Glasses","rare":false,"stages":[]},{"id":2262,"slot":"headgear","name":"Clown Nose","rare":false,"stages":["prontera"]},{"id":2264,"slot":"headgear","name":"Munak Hat","rare":false,"stages":["payon_cave"]},{"id":2268,"slot":"headgear","name":"Pipe","rare":false,"stages":["payon"]},{"id":2272,"slot":"headgear","name":"Stop Post","rare":false,"stages":["payon"]},{"id":2274,"slot":"headgear","name":"Ghost Bandana","rare":false,"stages":["sunken","payon_cave","orcs","pyramid"]},{"id":2277,"slot":"headgear","name":"Nurse Cap","rare":false,"stages":["payon_cave"]},{"id":2280,"slot":"headgear","name":"Sakkat","rare":false,"stages":[]},{"id":2282,"slot":"headgear","name":"Halo","rare":true,"stages":["payon"]},{"id":2285,"slot":"headgear","name":"Apple of Archer","rare":false,"stages":["payon_cave"]},{"id":2286,"slot":"headgear","name":"Elven Ears","rare":false,"stages":["sewer"]},{"id":2287,"slot":"headgear","name":"Pirate Bandana","rare":false,"stages":["sunken"]},{"id":2288,"slot":"headgear","name":"Mr. Scream","rare":false,"stages":["sewer"]},{"id":2289,"slot":"headgear","name":"Poo Poo Hat","rare":false,"stages":["payon"]},{"id":2291,"slot":"headgear","name":"Butterfly Mask","rare":false,"stages":[]},{"id":2292,"slot":"headgear","name":"Welding Mask","rare":false,"stages":["sewer"]},{"id":2296,"slot":"headgear","name":"Binoculars","rare":false,"stages":[]},{"id":2297,"slot":"headgear","name":"Goblin Mask","rare":false,"stages":[]},{"id":2298,"slot":"headgear","name":"Green Feeler","rare":false,"stages":["prontera"]},{"id":2299,"slot":"headgear","name":"Orc Helm","rare":false,"stages":[]},{"id":2302,"slot":"armor","name":"Cotton Shirt","rare":false,"stages":["prontera"]},{"id":2303,"slot":"armor","name":"Jacket","rare":false,"stages":["sewer"]},{"id":2304,"slot":"armor","name":"Jacket","rare":false,"stages":["sewer"]},{"id":2305,"slot":"armor","name":"Adventurer's Suit","rare":false,"stages":["payon_cave"]},{"id":2306,"slot":"armor","name":"Adventurer's Suit","rare":false,"stages":["prontera"]},{"id":2307,"slot":"armor","name":"Mantle","rare":false,"stages":[]},{"id":2308,"slot":"armor","name":"Mantle","rare":false,"stages":["sunken","payon","orcs"]},{"id":2311,"slot":"armor","name":"Mink Coat","rare":true,"stages":[]},{"id":2314,"slot":"armor","name":"Chain Mail","rare":false,"stages":[]},{"id":2316,"slot":"armor","name":"Full Plate","rare":false,"stages":[]},{"id":2320,"slot":"armor","name":"Formal Suit","rare":false,"stages":[]},{"id":2321,"slot":"armor","name":"Silk Robe","rare":false,"stages":["prontera"]},{"id":2324,"slot":"armor","name":"Scapulare","rare":false,"stages":["payon"]},{"id":2329,"slot":"armor","name":"Wooden Mail","rare":false,"stages":["payon"]},{"id":2330,"slot":"armor","name":"Tights","rare":false,"stages":[]},{"id":2333,"slot":"armor","name":"Silver Robe","rare":false,"stages":["sunken"]},{"id":2335,"slot":"armor","name":"Thief Clothes","rare":false,"stages":[]},{"id":2336,"slot":"armor","name":"Thief Clothes","rare":false,"stages":["sunken","orcs","pyramid"]},{"id":2337,"slot":"armor","name":"Ninja Suit","rare":false,"stages":["payon_cave"]},{"id":2353,"slot":"armor","name":"Odin's Blessing","rare":true,"stages":[]},{"id":2355,"slot":"armor","name":"Angelic Protection","rare":false,"stages":["prontera"]},{"id":2367,"slot":"armor","name":"Sniping Suit","rare":true,"stages":[]},{"id":2404,"slot":"shoes","name":"Shoes","rare":false,"stages":["payon_cave"]},{"id":2405,"slot":"shoes","name":"Boots","rare":false,"stages":["sunken"]},{"id":2406,"slot":"shoes","name":"Boots","rare":false,"stages":["sunken","payon_cave"]},{"id":2411,"slot":"shoes","name":"Greaves","rare":false,"stages":[]},{"id":2418,"slot":"shoes","name":"Vidar's Boots","rare":true,"stages":[]},{"id":2419,"slot":"shoes","name":"Goibne's Greaves","rare":true,"stages":[]},{"id":2420,"slot":"shoes","name":"Angel's Reincarnation","rare":false,"stages":["prontera"]},{"id":2424,"slot":"shoes","name":"Tidal Shoes","rare":false,"stages":["prontera","byalan"]},{"id":2503,"slot":"garment","name":"Muffler","rare":false,"stages":["sunken"]},{"id":2504,"slot":"garment","name":"Muffler","rare":false,"stages":["payon_cave"]},{"id":2505,"slot":"garment","name":"Manteau","rare":false,"stages":["sunken","byalan","payon","payon_cave"]},{"id":2507,"slot":"garment","name":"Cape of Ancient Lord","rare":true,"stages":[]},{"id":2509,"slot":"garment","name":"Manteau of Survival","rare":false,"stages":["byalan"]},{"id":2511,"slot":"garment","name":"Skeleton Manteau","rare":false,"stages":[]},{"id":2515,"slot":"garment","name":"Eagle Wing","rare":true,"stages":[]},{"id":2603,"slot":"accessory","name":"Necklace","rare":false,"stages":["byalan","payon_cave"]},{"id":2605,"slot":"accessory","name":"Brooch","rare":false,"stages":["byalan","payon","payon_cave"]},{"id":2607,"slot":"accessory","name":"Clip","rare":false,"stages":["prontera","sunken","byalan"]},{"id":2608,"slot":"accessory","name":"Rosary","rare":false,"stages":["payon_cave","pyramid"]},{"id":2609,"slot":"accessory","name":"Skull Ring","rare":false,"stages":["payon_cave"]},{"id":2610,"slot":"accessory","name":"Gold Ring","rare":false,"stages":["sewer"]},{"id":2614,"slot":"accessory","name":"Eye of Dullahan","rare":true,"stages":[]},{"id":2615,"slot":"accessory","name":"Safety Ring","rare":false,"stages":["sewer"]},{"id":2616,"slot":"accessory","name":"Critical Ring","rare":false,"stages":["sewer"]},{"id":2617,"slot":"accessory","name":"Celebrant's Mitten","rare":false,"stages":[]},{"id":2619,"slot":"accessory","name":"Bow Thimble","rare":false,"stages":[]},{"id":2620,"slot":"accessory","name":"Rogue's Treasure","rare":false,"stages":["sewer"]},{"id":2627,"slot":"accessory","name":"Belt","rare":false,"stages":["sewer"]},{"id":2678,"slot":"accessory","name":"Ring of Flame Lord","rare":true,"stages":[]},{"id":2679,"slot":"accessory","name":"Ring of Resonance","rare":true,"stages":[]},{"id":5008,"slot":"headgear","name":"Puppy Love","rare":false,"stages":["payon_cave"]},{"id":5012,"slot":"headgear","name":"Ph.D Hat","rare":false,"stages":[]},{"id":5013,"slot":"headgear","name":"Lord Kaho's Horn","rare":true,"stages":[]},{"id":5017,"slot":"headgear","name":"Bone Helm","rare":false,"stages":[]},{"id":5019,"slot":"headgear","name":"Corsair","rare":false,"stages":["sunken"]},{"id":5035,"slot":"headgear","name":"Poring Hat","rare":false,"stages":["prontera"]},{"id":5038,"slot":"headgear","name":"Deviruchi Hat","rare":true,"stages":[]},{"id":5046,"slot":"headgear","name":"Bongun Hat","rare":false,"stages":["payon_cave"]},{"id":13001,"slot":"weapon","name":"Dragon Killer","rare":true,"stages":[]},{"id":13007,"slot":"weapon","name":"Jitte","rare":false,"stages":[]},{"id":13011,"slot":"weapon","name":"Asura","rare":false,"stages":["prontera"]},{"id":13046,"slot":"weapon","name":"Krieg","rare":false,"stages":["payon"]},{"id":13104,"slot":"weapon","name":"Garrison","rare":false,"stages":["sunken"]},{"id":13150,"slot":"weapon","name":"Branch","rare":false,"stages":[]},{"id":13151,"slot":"weapon","name":"Cyclone","rare":false,"stages":["payon_cave"]},{"id":13156,"slot":"weapon","name":"Gate Keeper","rare":true,"stages":[]},{"id":13160,"slot":"weapon","name":"Destroyer","rare":true,"stages":[]},{"id":13301,"slot":"weapon","name":"Huuma Giant Wheel Shuriken","rare":false,"stages":[]},{"id":13303,"slot":"weapon","name":"Huuma Blaze Shuriken","rare":true,"stages":[]},{"id":22847,"slot":"accessory","name":"Prontera Patrol Badge","rare":false,"stages":["prt_castle"]}],"cards":[{"id":4001,"name":"Poring Card","slot":"armor","stages":["prontera"]},{"id":4006,"name":"Lunatic Card","slot":"garment","stages":["prontera"]},{"id":4002,"name":"Fabre Card","slot":"armor","stages":["prontera"]},{"id":4004,"name":"Drops Card","slot":"accessory","stages":["prontera"]},{"id":4009,"name":"Chonchon Card","slot":"garment","stages":[]},{"id":4021,"name":"Rocker Card","slot":"accessory","stages":["prontera"]},{"id":4010,"name":"Willow Card","slot":"headgear","stages":["payon"]},{"id":4015,"name":"Condor Card","slot":"accessory","stages":["prontera"]},{"id":4022,"name":"Spore Card","slot":"armor","stages":["payon"]},{"id":4033,"name":"PoPoring Card","slot":"headgear","stages":["payon","payon_cave"]},{"id":4017,"name":"Savage Bebe Card","slot":"weapon","stages":["prontera"]},{"id":4044,"name":"Smokie Card","slot":"accessory","stages":["payon"]},{"id":4029,"name":"Wolf Card","slot":"weapon","stages":["payon","orcs"]},{"id":4066,"name":"Orc Warrior Card","slot":"shield","stages":["prt_castle","orcs"]},{"id":4060,"name":"Goblin Card","slot":"weapon","stages":["orcs"]},{"id":4091,"name":"Kobold Card","slot":"weapon","stages":["orcs"]},{"id":4038,"name":"Zombie Card","slot":"armor","stages":["payon_cave","pyramid"]},{"id":4085,"name":"Orc Skeleton Card","slot":"weapon","stages":["pyramid"]},{"id":4054,"name":"Angelring Card","slot":"armor","stages":["payon"]},{"id":4174,"name":"Devilring Card","slot":"garment","stages":["payon","pyramid"]},{"id":4047,"name":"Ghostring Card","slot":"armor","stages":["sunken","orcs","pyramid"]},{"id":4123,"name":"Eddga Card","slot":"shoes","stages":["payon"]},{"id":4143,"name":"Orc Hero Card","slot":"headgear","stages":["orcs"]},{"id":4144,"name":"Osiris Card","slot":"accessory","stages":["pyramid"]},{"id":4147,"name":"Baphomet Card","slot":"weapon","stages":[]},{"id":4003,"name":"Pupa Card","slot":"armor","stages":[]},{"id":4008,"name":"Picky Card","slot":"armor","stages":["prontera"]},{"id":4007,"name":"Pecopeco Egg Card","slot":"armor","stages":[]},{"id":4012,"name":"Thiefbug Egg Card","slot":"armor","stages":["sewer"]},{"id":4019,"name":"Hornet Card","slot":"weapon","stages":["prontera"]},{"id":4020,"name":"Familiar Card","slot":"weapon","stages":["sewer"]},{"id":4023,"name":"Baby Desert Wolf Card","slot":"weapon","stages":["prontera"]},{"id":4024,"name":"Plankton Card","slot":"weapon","stages":["sewer"]},{"id":4266,"name":"Eclipse Card","slot":"garment","stages":["prontera"]},{"id":4211,"name":"Vocal Card","slot":"headgear","stages":["prontera"]},{"id":4197,"name":"Mastering Card","slot":"accessory","stages":["prontera"]},{"id":4128,"name":"Golden Thiefbug Card","slot":"shield","stages":["sewer"]},{"id":4016,"name":"Thief Bug Card","slot":"armor","stages":["sewer"]},{"id":4026,"name":"Female Thiefbug Card","slot":"weapon","stages":["sewer"]},{"id":4014,"name":"Roda Frog Card","slot":"armor","stages":["prontera"]},{"id":4040,"name":"Creamy Card","slot":"accessory","stages":["prontera"]},{"id":4030,"name":"Mandragora Card","slot":"weapon","stages":["prontera"]},{"id":4306,"name":"Toad Card","slot":"garment","stages":["prontera"]},{"id":4179,"name":"Dragonfly Card","slot":"garment","stages":["prontera"]},{"id":4028,"name":"Tarou Card","slot":"accessory","stages":["sewer"]},{"id":4069,"name":"Drainliar Card","slot":"weapon","stages":["sewer"]},{"id":4296,"name":"Cramp Card","slot":"headgear","stages":["sewer"]},{"id":4027,"name":"Kukre Card","slot":"accessory","stages":["sunken"]},{"id":4055,"name":"Marina Card","slot":"weapon","stages":["sunken"]},{"id":4035,"name":"Hydra Card","slot":"weapon","stages":["sunken"]},{"id":4102,"name":"Whisper Card","slot":"garment","stages":["sunken"]},{"id":4314,"name":"Penomena Card","slot":"shield","stages":["sunken"]},{"id":4089,"name":"Swordfish Card","slot":"armor","stages":["sunken"]},{"id":4073,"name":"Pirate Skel Card","slot":"accessory","stages":["sunken"]},{"id":4137,"name":"Drake Card","slot":"weapon","stages":["sunken"]},{"id":4049,"name":"Vadon Card","slot":"weapon","stages":["byalan"]},{"id":4061,"name":"Cornutus Card","slot":"armor","stages":["byalan"]},{"id":4095,"name":"Marse Card","slot":"garment","stages":["byalan"]},{"id":4077,"name":"Phen Card","slot":"accessory","stages":["byalan"]},{"id":4093,"name":"Obeaune Card","slot":"accessory","stages":["byalan"]},{"id":4084,"name":"Marine Sphere Card","slot":"accessory","stages":["byalan"]},{"id":4199,"name":"Merman Card","slot":"accessory","stages":["byalan"]},{"id":4125,"name":"Deviace Card","slot":"weapon","stages":["byalan"]},{"id":4111,"name":"Strouf Card","slot":"weapon","stages":["byalan"]},{"id":4524,"name":"King Dramoh Card","slot":"headgear","stages":["byalan"]},{"id":4525,"name":"Kraken Card","slot":"garment","stages":["byalan"]},{"id":4037,"name":"Snake Card","slot":"weapon","stages":["payon"]},{"id":4034,"name":"Wormtail Card","slot":"accessory","stages":["payon"]},{"id":4048,"name":"Poison Spore Card","slot":"accessory","stages":["payon"]},{"id":4052,"name":"Elder Willow Card","slot":"headgear","stages":["payon"]},{"id":4074,"name":"Bigfoot Card","slot":"shield","stages":["payon"]},{"id":4098,"name":"Dokkaebi Card","slot":"armor","stages":["payon"]},{"id":4159,"name":"Nine Tail Card","slot":"garment","stages":["payon","payon_cave"]},{"id":4283,"name":"Greatest General Card","slot":"accessory","stages":["payon"]},{"id":4178,"name":"Dragon Tail Card","slot":"garment","stages":["payon"]},{"id":4183,"name":"Wandering Wolf Card","slot":"garment","stages":["payon"]},{"id":4131,"name":"Moonlight Flower Card","slot":"shoes","stages":["payon_cave"]},{"id":4025,"name":"Skeleton Card","slot":"weapon","stages":["payon_cave"]},{"id":4094,"name":"Archer Skeleton Card","slot":"weapon","stages":["payon_cave"]},{"id":4086,"name":"Soldier Skeleton Card","slot":"weapon","stages":["payon_cave"]},{"id":4090,"name":"Munak Card","slot":"shield","stages":["payon_cave"]},{"id":4212,"name":"Bongun Card","slot":"accessory","stages":["payon_cave"]},{"id":4100,"name":"Sohee Card","slot":"shoes","stages":["payon_cave"]},{"id":4103,"name":"Horong Card","slot":"accessory","stages":["payon_cave"]},{"id":4221,"name":"Skeleton General Card","slot":"shoes","stages":["payon_cave"]},{"id":4290,"name":"Cat O' Nine Tails Card","slot":"shoes","stages":["payon_cave"]},{"id":4328,"name":"Yao Jun Card","slot":"garment","stages":["payon_cave"]}],"pets":[{"id":"poring","name":"Poring","egg":9001,"obtain":"egg_drop","stages":["prontera"]},{"id":"lunatic","name":"Lunatic","egg":9004,"obtain":"egg_drop","stages":["prontera"]},{"id":"drops","name":"Drops","egg":9002,"obtain":"egg_drop","stages":["prontera"]},{"id":"picky","name":"Picky","egg":9005,"obtain":"egg_drop","stages":["prontera"]},{"id":"savage_babe","name":"Savage Babe","egg":9009,"obtain":"egg_drop","stages":["prontera"]},{"id":"baby_desert_wolf","name":"Baby Desert Wolf","egg":9010,"obtain":"egg_drop","stages":["prontera"]},{"id":"rocker","name":"Rocker","egg":9011,"obtain":"egg_drop","stages":["prontera"]},{"id":"familiar","name":"Familiar","egg":9138,"obtain":"egg_drop","stages":["sewer"]},{"id":"mastering","name":"Mastering","egg":9069,"obtain":"evolution","stages":[]},{"id":"whisper","name":"Whisper","egg":9045,"obtain":"egg_drop","stages":["sunken"]},{"id":"spore","name":"Spore","egg":9012,"obtain":"egg_drop","stages":["payon"]},{"id":"poison_spore","name":"Poison Spore","egg":9013,"obtain":"egg_drop","stages":["payon"]},{"id":"poporing","name":"Poporing","egg":9003,"obtain":"egg_drop","stages":["payon","payon_cave"]},{"id":"smokie","name":"Smokie","egg":9015,"obtain":"egg_drop","stages":["payon"]},{"id":"dokebi","name":"Dokebi","egg":9019,"obtain":"egg_drop","stages":["payon"]},{"id":"nine_tail","name":"Nine Tail","egg":9095,"obtain":"egg_drop","stages":["payon","payon_cave"]},{"id":"willow","name":"Willow","egg":9103,"obtain":"egg_drop","stages":["payon"]},{"id":"angeling","name":"Angeling","egg":9088,"obtain":"evolution","stages":[]},{"id":"munak","name":"Munak","egg":9018,"obtain":"egg_drop","stages":["payon_cave"]},{"id":"bon_gun","name":"Bongun","egg":9025,"obtain":"egg_drop","stages":["payon_cave"]},{"id":"sohee","name":"Sohee","egg":9020,"obtain":"egg_drop","stages":["payon_cave"]},{"id":"hyegun","name":"Hyegun","egg":9093,"obtain":"evolution","stages":[]},{"id":"cat_o_nine_tail","name":"Cat O' Nine Tails","egg":9096,"obtain":"evolution","stages":[]},{"id":"moonlight","name":"Moonlight Flower","egg":9112,"obtain":"egg_drop","stages":["payon_cave"]}],"stages":[{"id":"prontera","names":{"es":"Campos de Prontera","en":"Prontera Fields","zh-TW":"普隆德拉原野","pt-BR":"Campos de Prontera"},"levels":"1–8","farmable":true},{"id":"sewer","names":{"es":"Alcantarillas de Prontera","en":"Prontera Culverts","zh-TW":"普隆德拉地下水道","pt-BR":"Esgotos de Prontera"},"levels":"9–12","farmable":true},{"id":"sunken","names":{"es":"Barco hundido","en":"Sunken Ship","zh-TW":"失事輪","pt-BR":"Navio Naufragado"},"levels":"13–15","farmable":true},{"id":"byalan","names":{"es":"Isla de Byalan","en":"Byalan Island","zh-TW":"柏伊亞嵐島","pt-BR":"Ilha de Byalan"},"levels":"16–20","farmable":true},{"id":"payon","names":{"es":"Bosque de Payon","en":"Payon Forest","zh-TW":"斐揚森林","pt-BR":"Floresta de Payon"},"levels":"21–25","farmable":true},{"id":"payon_cave","names":{"es":"Cueva de Payon","en":"Payon Cave","zh-TW":"斐揚洞穴","pt-BR":"Caverna de Payon"},"levels":"26–30","farmable":true},{"id":"prt_castle","names":{"es":"Castillo de Prontera","en":"Prontera Castle","zh-TW":"普隆德拉城","pt-BR":"Castelo de Prontera"},"levels":"31–35","farmable":false},{"id":"orcs","names":{"es":"Aldea orca","en":"Orc Village","zh-TW":"獸人村","pt-BR":"Vila dos Orcos"},"levels":"31–40","farmable":false},{"id":"pyramid","names":{"es":"Pirámides de Morroc","en":"Morroc Pyramids","zh-TW":"夢羅克金字塔","pt-BR":"Pirâmides de Morroc"},"levels":"41–50","farmable":false}],"qualities":[{"id":0,"cls":"r0","color":"#f2f2f2","names":{"es":"Común","en":"Common","zh-TW":"普通","pt-BR":"Comum"}},{"id":1,"cls":"r1","color":"#3ddc5a","names":{"es":"Poco común","en":"Uncommon","zh-TW":"優良","pt-BR":"Incomum"}},{"id":2,"cls":"r2","color":"#2f7bff","names":{"es":"Raro","en":"Rare","zh-TW":"稀有","pt-BR":"Raro"}},{"id":3,"cls":"r3","color":"#a040ff","names":{"es":"Épico","en":"Epic","zh-TW":"史詩","pt-BR":"Épico"}},{"id":4,"cls":"r4","color":"#ff9a2e","names":{"es":"Legendario","en":"Legendary","zh-TW":"傳說","pt-BR":"Lendário"}}],"filters":[{"id":"all","slots":null,"names":{"es":"Todo","en":"All","zh-TW":"全部","pt-BR":"Tudo"}},{"id":"weapon","slots":["weapon"],"names":{"es":"Armas","en":"Weapons","zh-TW":"武器","pt-BR":"Armas"}},{"id":"head","slots":["headgear"],"names":{"es":"Cabeza","en":"Head","zh-TW":"頭部","pt-BR":"Cabeça"}},{"id":"armor","slots":["armor"],"names":{"es":"Armadura","en":"Armor","zh-TW":"護甲","pt-BR":"Armadura"}},{"id":"shield","slots":["shield"],"names":{"es":"Escudo","en":"Shield","zh-TW":"盾牌","pt-BR":"Escudo"}},{"id":"garment","slots":["garment"],"names":{"es":"Capa","en":"Garment","zh-TW":"披肩","pt-BR":"Capa"}},{"id":"shoes","slots":["shoes"],"names":{"es":"Calzado","en":"Footgear","zh-TW":"鞋子","pt-BR":"Calçados"}},{"id":"acc","slots":["accessory"],"names":{"es":"Accesorios","en":"Accessories","zh-TW":"飾品","pt-BR":"Acessórios"}}],"cardFilters":[{"id":"all","slot":null,"names":{"es":"Todo","en":"All","zh-TW":"全部","pt-BR":"Tudo"}},{"id":"weapon","slot":"weapon","names":{"es":"Arma","en":"Weapon","zh-TW":"武器","pt-BR":"Arma"}},{"id":"headgear","slot":"headgear","names":{"es":"Casco","en":"Headgear","zh-TW":"頭飾","pt-BR":"Elmo"}},{"id":"armor","slot":"armor","names":{"es":"Armadura","en":"Armor","zh-TW":"護甲","pt-BR":"Armadura"}},{"id":"shield","slot":"shield","names":{"es":"Escudo","en":"Shield","zh-TW":"盾牌","pt-BR":"Escudo"}},{"id":"garment","slot":"garment","names":{"es":"Capa","en":"Garment","zh-TW":"披肩","pt-BR":"Capa"}},{"id":"shoes","slot":"shoes","names":{"es":"Calzado","en":"Footgear","zh-TW":"鞋子","pt-BR":"Calçados"}},{"id":"accessory","slot":"accessory","names":{"es":"Accesorio","en":"Accessory","zh-TW":"飾品","pt-BR":"Acessório"}}],"affixes":[{"id":"str","names":{"es":"Fuerza","en":"Strength","zh-TW":"力量","pt-BR":"Força"}},{"id":"agi","names":{"es":"Agilidad","en":"Agility","zh-TW":"敏捷","pt-BR":"Agilidade"}},{"id":"vit","names":{"es":"Vitalidad","en":"Vitality","zh-TW":"體力","pt-BR":"Vitalidade"}},{"id":"int","names":{"es":"Inteligencia","en":"Intelligence","zh-TW":"智力","pt-BR":"Inteligência"}},{"id":"dex","names":{"es":"Destreza","en":"Dexterity","zh-TW":"靈巧","pt-BR":"Destreza"}},{"id":"luk","names":{"es":"Suerte","en":"Luck","zh-TW":"幸運","pt-BR":"Sorte"}},{"id":"crit","names":{"es":"Crítico","en":"Crit","zh-TW":"暴擊","pt-BR":"Crítico"}},{"id":"pierce","names":{"es":"Perforación","en":"Pierce","zh-TW":"貫穿","pt-BR":"Perfuração"}},{"id":"cd","names":{"es":"Reutilización","en":"Cooldown","zh-TW":"冷卻","pt-BR":"Recarga"}},{"id":"area","names":{"es":"Área","en":"Area","zh-TW":"範圍","pt-BR":"Área"}},{"id":"hp","names":{"es":"HP","en":"HP","zh-TW":"HP","pt-BR":"HP"}},{"id":"armor","names":{"es":"Armadura","en":"Armor","zh-TW":"防禦","pt-BR":"Armadura"}},{"id":"spd","names":{"es":"Velocidad","en":"Speed","zh-TW":"移動速度","pt-BR":"Velocidade"}},{"id":"flee","names":{"es":"Flee","en":"Flee","zh-TW":"迴避","pt-BR":"Flee"}},{"id":"dmg","names":{"es":"Daño","en":"Damage","zh-TW":"傷害","pt-BR":"Dano"}},{"id":"cast","names":{"es":"Lanzamiento","en":"Cast","zh-TW":"詠唱","pt-BR":"Lançamento"}},{"id":"regen","names":{"es":"Regeneración","en":"Regen","zh-TW":"回復","pt-BR":"Regeneração"}},{"id":"pickup","names":{"es":"Recogida","en":"Pickup","zh-TW":"拾取","pt-BR":"Coleta"}},{"id":"exp","names":{"es":"EXP","en":"EXP","zh-TW":"EXP","pt-BR":"EXP"}},{"id":"zeny","names":{"es":"Zeny","en":"Zeny","zh-TW":"Zeny","pt-BR":"Zeny"}},{"id":"dodge","names":{"es":"Esquiva","en":"Dodge","zh-TW":"完全迴避","pt-BR":"Esquiva"}}]};

  const STORE_KEY = "ro-survivors.tm-skill-plan.v2";
  const STORE_OLD = "ro-survivors.tm-skill-plan.v1";
  const ICON = (id) => `/assets/icons/${id}.png`;
  const ITEM_ICON = (it) => it.img ? `/assets/${it.img}` : `/assets/items/${it.icon}.png`;
  const JOBS = Object.fromEntries(DATA.jobs.map((j) => [j.id, j]));
  const SECOND = new Set(DATA.jobs.filter((j) => j.tier === "second" || j.rank === 2).map((j) => j.id));
  const ASPECTS = DATA.aspects.slice();
  const SKILL_EFFECTS = {
    bash: [{id:"stun",names:{"es":"Probabilidad de aturdir","en":"Stun chance","zh-TW":"暈眩機率","pt-BR":"Chance de atordoar"}}],
    provoke: [{id:"mark",names:{"es":"Daño extra que reciben","en":"Extra damage taken","zh-TW":"額外受到傷害","pt-BR":"Dano extra recebido"}}],
    demoralizing_shout: [{id:"weaken",names:{"es":"Daño que pierden","en":"Damage lost","zh-TW":"損失傷害","pt-BR":"Dano perdido"}}],
    endure: [{id:"reduction",names:{"es":"Reducción de daño del buff","en":"Buff damage reduction","zh-TW":"增益傷害減免","pt-BR":"Redução de dano do efeito"}}],
    hp_recovery: [{id:"heal",names:{"es":"HP regenerados","en":"HP regenerated","zh-TW":"回復的 HP","pt-BR":"HP regenerado"}}],
    coldbolt: [{id:"slow",names:{"es":"Ralentización","en":"Slow","zh-TW":"緩速","pt-BR":"Lentidão"}},{id:"freeze",names:{"es":"Probabilidad de congelar","en":"Freeze chance","zh-TW":"冰凍機率","pt-BR":"Chance de congelar"}}],
    frost_diver: [{id:"freeze",names:{"es":"Congelación","en":"Freeze","zh-TW":"冰凍","pt-BR":"Congelamento"}}],
    concentration: [{id:"agiDex",names:{"es":"AGI y DEX del buff","en":"Buff AGI and DEX","zh-TW":"增益 AGI 與 DEX","pt-BR":"AGI e DES do efeito"}}],
    heal: [{id:"heal",names:{"es":"Curación","en":"Healing","zh-TW":"治療","pt-BR":"Cura"}}],
    decrease_agi: [{id:"slow",names:{"es":"Ralentización","en":"Slow","zh-TW":"緩速","pt-BR":"Lentidão"}}],
    signum_crucis: [{id:"holy",names:{"es":"Daño sagrado extra que reciben","en":"Extra holy damage taken","zh-TW":"受到的神聖傷害增加","pt-BR":"Dano sagrado extra recebido"}}],
    aqua_benedicta: [{id:"heal",names:{"es":"Curación por segundo","en":"Healing per second","zh-TW":"每秒治療","pt-BR":"Cura por segundo"}}],
    blessing: [{id:"dmg",names:{"es":"Daño del buff","en":"Buff damage","zh-TW":"增益傷害","pt-BR":"Dano do efeito"}},{id:"cast",names:{"es":"Rapidez de casteo del buff","en":"Buff cast speed","zh-TW":"增益詠唱速度","pt-BR":"Velocidade de conjuração do efeito"}}],
    holy_smite: [{id:"fervor",names:{"es":"Ataques básicos bendecidos","en":"Blessed basic attacks","zh-TW":"受祝福的普通攻擊","pt-BR":"Ataques básicos abençoados"}}],
    envenom: [{id:"poison",names:{"es":"Daño del veneno","en":"Poison damage","zh-TW":"毒傷害","pt-BR":"Dano do veneno"}}],
    sand_attack: [{id:"blind",names:{"es":"Ceguera","en":"Blindness","zh-TW":"致盲","pt-BR":"Cegueira"}}],
    poison_bomb: [{id:"poison",names:{"es":"Daño del veneno","en":"Poison damage","zh-TW":"毒傷害","pt-BR":"Dano do veneno"}}],
    shadowstep: [{id:"stun",names:{"es":"Aturdimiento","en":"Stun","zh-TW":"暈眩","pt-BR":"Atordoamento"}},{id:"flee",names:{"es":"Flee del buff","en":"Buff Flee","zh-TW":"增益迴避","pt-BR":"Esquiva do efeito"}}],
    throw_stone: [{id:"stun",names:{"es":"Aturdimiento","en":"Stun","zh-TW":"暈眩","pt-BR":"Atordoamento"}}],
    hiding: [{id:"dmg",names:{"es":"Daño al salir","en":"Damage on exit","zh-TW":"離開時傷害","pt-BR":"Dano ao sair"}}],
    heel_drop: [{id:"stun",names:{"es":"Aturdimiento","en":"Stun","zh-TW":"暈眩","pt-BR":"Atordoamento"}}],
    sprint: [{id:"speed",names:{"es":"Velocidad del buff","en":"Buff movement speed","zh-TW":"增益移動速度","pt-BR":"Velocidade de movimento do efeito"}}],
    charge_attack: [{id:"stun",names:{"es":"Aturdimiento","en":"Stun","zh-TW":"暈眩","pt-BR":"Atordoamento"}}],
    spear_quicken: [{id:"haste",names:{"es":"Celeridad","en":"Haste","zh-TW":"冷卻縮減","pt-BR":"Aceleração"}}],
    shield_charge: [{id:"stun",names:{"es":"Probabilidad de aturdir","en":"Stun chance","zh-TW":"暈眩機率","pt-BR":"Chance de atordoar"}}],
    auto_guard: [{id:"block",names:{"es":"Probabilidad de bloquear","en":"Block chance","zh-TW":"格擋機率","pt-BR":"Chance de bloquear"}}],
    meteor_storm: [{id:"stun",names:{"es":"Probabilidad de aturdir","en":"Stun chance","zh-TW":"暈眩機率","pt-BR":"Chance de atordoar"}}],
    frost_nova: [{id:"freeze",names:{"es":"Probabilidad de congelar","en":"Freeze chance","zh-TW":"冰凍機率","pt-BR":"Chance de congelar"}}],
    storm_gust: [{id:"freeze",names:{"es":"Probabilidad de congelar","en":"Freeze chance","zh-TW":"冰凍機率","pt-BR":"Chance de congelar"}}],
    lord_of_vermilion: [{id:"blind",names:{"es":"Probabilidad de cegar","en":"Blind chance","zh-TW":"致盲機率","pt-BR":"Chance de cegar"}}],
    hindsight: [{id:"time",names:{"es":"Duración","en":"Duration","zh-TW":"持續時間","pt-BR":"Duração"}}],
    detecting: [{id:"mark",names:{"es":"Daño extra que reciben","en":"Extra damage taken","zh-TW":"額外受到傷害","pt-BR":"Dano extra recebido"}}],
    sandman: [{id:"sleep",names:{"es":"Sueño","en":"Sleep","zh-TW":"睡眠","pt-BR":"Sono"}}],
    magnificat: [{id:"haste",names:{"es":"Celeridad","en":"Haste","zh-TW":"冷卻縮減","pt-BR":"Aceleração"}}],
    rush_quake: [{id:"stun",names:{"es":"Probabilidad de aturdir","en":"Stun chance","zh-TW":"暈眩機率","pt-BR":"Chance de atordoar"}}],
    estun: [{id:"stun",names:{"es":"Aturdimiento","en":"Stun","zh-TW":"暈眩","pt-BR":"Atordoamento"}}],
  };
  for (const [sid, effs] of Object.entries(SKILL_EFFECTS)) {
    if (DATA.skills[sid]) DATA.skills[sid].effects = effs;
  }
  const RUN = Object.fromEntries(DATA.runItems.map((it) => [it.id, it]));
  const SLOTS = DATA.slots.map((s) => s.id);
  const LEVEL_UP = new Set([
    "¡Level Up!", "Level Up!", "升級！", "Subiu de nível!",
    DATA.i18n.ui["¡Level Up!"]?.en, DATA.i18n.ui["¡Level Up!"]?.["zh-TW"], DATA.i18n.ui["¡Level Up!"]?.["pt-BR"],
  ].filter(Boolean));
  const CHEST_TITLE = new Set([
    "Cofre del tesoro", "Treasure chest", "寶箱", "Baú do tesouro",
    DATA.i18n.ui["Cofre del tesoro"]?.en, DATA.i18n.ui["Cofre del tesoro"]?.["zh-TW"], DATA.i18n.ui["Cofre del tesoro"]?.["pt-BR"],
  ].filter(Boolean));

  const LANGS = ["zh-TW", "en", "es", "pt-BR"];

  function gameLang() {
    try {
      const s = JSON.parse(localStorage.getItem("ro-survivors:settings") || "{}");
      const raw = String(s.lang || "").toLowerCase();
      if (raw.startsWith("zh")) return "zh-TW";
      if (raw) return "en";
    } catch (_) {}
    const n = (navigator.language || "").toLowerCase();
    return n.startsWith("zh") ? "zh-TW" : "en";
  }

  let lang = gameLang();

  function applyGameLang(rerender) {
    const next = gameLang();
    if (next === lang) return false;
    lang = next;
    if (rerender) {
      refreshBtn();
      const ov = document.getElementById("ros-plan-ov");
      if (ov && !ov.classList.contains("hidden")) renderWindow();
      const asp = document.getElementById("ros-asp");
      if (asp && !asp.classList.contains("hidden")) {
        if (perkPopKind) openPerkPopup(perkPopKind);
        else if (aspSkill) openAspectPopup(aspSkill);
      }
    }
    return true;
  }


  const COPY = {
    plan: { "zh-TW": "提前規劃", en: "Plan Ahead", es: "Plan anticipado", "pt-BR": "Planejamento antecipado" },
    pickJob: { "zh-TW": "選擇職業", en: "Choose a job", es: "Elegir profesión", "pt-BR": "Escolher classe" },
    noJobHint: { "zh-TW": "尚未選擇職業，點擊此處選擇職業", en: "No job selected yet. Tap here to choose a job.", es: "Aún no has elegido profesión. Toca aquí para elegir.", "pt-BR": "Nenhuma classe selecionada. Toque aqui para escolher." },
    pickJobFirst: { "zh-TW": "請先點擊上方「選擇職業」以設定技能與寶箱規劃", en: "Tap \"Choose a job\" above first to configure skills & chest.", es: "Toca primero «Elegir profesión» arriba para configurar.", "pt-BR": "Toque primeiro em \"Escolher classe\" acima para configurar." },
    back: { "zh-TW": "返回", en: "Back", es: "Volver", "pt-BR": "Voltar" },
    autoPick: { "zh-TW": "關卡內自動選擇", en: "Auto-pick in stages", es: "Selección automática", "pt-BR": "Seleção automática" },
    autoMove: { "zh-TW": "關卡內自動移動", en: "Auto-move in stages", es: "Movimiento automático", "pt-BR": "Movimento automático" },
    skills: { "zh-TW": "技能", en: "Skills", es: "Habilidades", "pt-BR": "Habilidades" },
    build: { "zh-TW": "技能與寶箱", en: "Skills & chest", es: "Habilidades y cofre", "pt-BR": "Habilidades e baú" },
    chest: { "zh-TW": "寶箱", en: "Treasure chest", es: "Cofre", "pt-BR": "Baú" },
    enhance: { "zh-TW": "技能強化", en: "Skill upgrades", es: "Mejoras de habilidad", "pt-BR": "Aprimoramentos" },
    rotate: { "zh-TW": "選擇第一個出戰技能", en: "After picking the 1st loadout skill", es: "Tras elegir la 1.ª habilidad", "pt-BR": "Após escolher a 1.ª habilidade" },
    rotateAfter: { "zh-TW": "次後，會依第二、三、四或普攻來循環選擇。", en: "times, cycle through 2nd, 3rd, 4th, or basic attack.", es: "veces, alterna entre 2.ª, 3.ª, 4.ª o ataque básico.", "pt-BR": "vezes, alterne entre 2.ª, 3.ª, 4.ª ou ataque básico." },
    noAspect: { "zh-TW": "此技能沒有技能強化。", en: "This skill has no upgrades.", es: "Esta habilidad no tiene mejoras.", "pt-BR": "Esta habilidade não tem aprimoramentos." },
    picked: { "zh-TW": "已選", en: "Picked", es: "Elegido", "pt-BR": "Escolhido" },
    loadout: { "zh-TW": "出戰技能", en: "Loadout", es: "Habilidades", "pt-BR": "Habilidades" },
    loadoutHint: { "zh-TW": "可點擊出戰技能來選擇強化項的優先度", en: "Tap loadout skills to set upgrade aspect priority", es: "Toca las habilidades equipadas para priorizar sus mejoras", "pt-BR": "Toque nas habilidades equipadas para priorizar melhorias" },
    pool: { "zh-TW": "可選技能", en: "Available skills", es: "Habilidades disponibles", "pt-BR": "Habilidades disponíveis" },
    poolHint: { "zh-TW": "在下方選擇四個技能作為出戰技能", en: "Select up to four skills below for your loadout", es: "Elige abajo cuatro habilidades para tu equipo", "pt-BR": "Escolha abaixo quatro habilidades para seu loadout" },
    firstJobs: { "zh-TW": "一轉", en: "First job", es: "1.ª profesión", "pt-BR": "1.ª classe" },
    secondJobs: { "zh-TW": "二轉", en: "Second job", es: "2.ª profesión", "pt-BR": "2.ª classe" },
    remove: { "zh-TW": "移除", en: "Remove", es: "Quitar", "pt-BR": "Remover" },
    chestHint: { "zh-TW": "為各欄位排出優先順序，寶箱出現對應道具時會自動選取。", en: "Set a priority list per slot; matching chest cards are auto-picked.", es: "Ordena cada ranura; se elegirán las cartas del cofre que coincidan.", "pt-BR": "Defina a prioridade de cada espaço; cartas correspondentes do baú serão escolhidas." },
    skillDeity: { "zh-TW": "各職業神祇", en: "Deity by job", es: "Deity por job", "pt-BR": "Divindade por classe" },
    statDeity: { "zh-TW": "屬性神祇", en: "Stat Deity", es: "Deity de stats", "pt-BR": "Divindade de atributos" },
    skillDeityHint: { "zh-TW": "已選擇職業神祇時，寶箱會優先選取職業神祇，其次才是屬性神祇。", en: "If a job Deity is selected, the chest prefers it over any Stat Deity.", es: "Si eliges una Deity de job, el cofre la prioriza frente a cualquier Deity de stats.", "pt-BR": "Se uma Divindade de classe estiver escolhida, o baú a prioriza em relação às Divindades de atributos." },
    skillDeitySub: { "zh-TW": "(職業神祇只能選擇一個，沒有順序功能)", en: "(You can only pick one job Deity; it has no order)", es: "(Solo puedes elegir una Deity de job; no tiene orden)", "pt-BR": "(Só é possível escolher uma Divindade de classe; não há ordem)" },
    exile: { "zh-TW": "放逐", en: "Banish", es: "Banish", "pt-BR": "Banish" },
    basicAttack: { "zh-TW": "普通攻擊", en: "Basic attack", es: "Ataque básico", "pt-BR": "Ataque básico" },
    basicOn: { "zh-TW": "自動選擇普通攻擊", en: "Auto-pick basic attack", es: "Elegir ataque básico", "pt-BR": "Escolher ataque básico" },
    basicOnDesc: { "zh-TW": "開啟後才會把普通攻擊當作出戰技能自動選擇與強化", en: "When on, basic attack is treated as a loadout skill for auto-pick and upgrades", es: "Si está activo, el ataque básico cuenta como habilidad de carga", "pt-BR": "Quando ativo, o ataque básico conta como habilidade de loadout" },
    rerollAll: { "zh-TW": "重抽全部", en: "Reroll deck", es: "Reroll deck", "pt-BR": "Reroll deck" },
    rerollCard: { "zh-TW": "重抽卡片", en: "Reroll card", es: "Reroll card", "pt-BR": "Reroll card" },
    focus: { "zh-TW": "專注", en: "Focus" },
    perkRerollAllDesc: { "zh-TW": "將升級或寶箱的卡片全部換成新的。", en: "Swaps the cards of a level-up or a chest for new ones." },
    perkRerollCardDesc: { "zh-TW": "重抽一張卡片：同一技能的不同強化，或同一寶箱欄位的不同裝備。", en: "Rerolls one card: same skill with a different upgrade, or the same chest slot with a different piece." },
    perkExileDesc: { "zh-TW": "在本局剩餘時間內，將某個技能或物品移出抽選；若已擁有，則不再出現它的強化。", en: "Removes a skill or item from the rolls for the rest of the run; if you already have it, it stops showing up for upgrades." },
    perkFocusDesc: { "zh-TW": "在本局剩餘時間內，某個技能或物品會優先出現在抽選中（×3）。", en: "A skill or item shows up with priority in the rolls (×3) for the rest of the run." },
    rerollOnlyUnplanned: { "zh-TW": "(只重抽沒勾選優先度的技能或道具)", en: "(Only rerolls skills or items without a checked priority)" },
    equip: { "zh-TW": "裝備", en: "Equipment", es: "Equipo", "pt-BR": "Equipamento" },
    cards: { "zh-TW": "卡片", en: "Cards", es: "Cartas", "pt-BR": "Cartas" },
    pets: { "zh-TW": "寵物", en: "Pets", es: "Mascotas", "pt-BR": "Mascotes" },
    farm: { "zh-TW": "自動刷取", en: "Auto-farm", es: "Recolectar", "pt-BR": "Farmar" },
    diffLoot: { "zh-TW": "戰利品", en: "Loot", es: "Botín", "pt-BR": "Saque" },
    farmHint: { "zh-TW": "先點選項目再按新增。三類合計只能指定一個目標。開啟後會自動關掉拾取視窗，並在關卡結束後再進入。", en: "Tap an item, then press Add. Only one farm target can be set across equipment, cards, and pets. After you turn auto-farm on, pickup windows close on their own and the stage is re-entered until it drops.", es: "Toca un objeto y pulsa Añadir. Solo puede haber un objetivo entre equipo, cartas y mascotas. Al activar la recolección, se cierra la ventana de recogida y se vuelve a entrar hasta que salga.", "pt-BR": "Toque um item e pressione Adicionar. Só pode haver um alvo entre equipamento, cartas e pets. Com o farm ligado, a janela de coleta fecha sozinha e o estágio é reaberto até dropar." },
    farmAuto: { "zh-TW": "全部", en: "All", es: "Todo", "pt-BR": "Tudo" },
    farmMissingItems: { "zh-TW": "缺少的裝備", en: "Missing gear", es: "Equipo que te falta", "pt-BR": "Equipamento que falta" },
    farmAllItems: { "zh-TW": "全部的裝備", en: "All gear", es: "Todo el equipo", "pt-BR": "Todo o equipamento" },
    farmShowingMissing: { "zh-TW": "目前顯示角色還沒有的項目", en: "Showing items this character does not have yet", es: "Mostrando lo que este personaje aún no tiene", "pt-BR": "Mostrando o que este personagem ainda não tem" },
    farmShowingAll: { "zh-TW": "目前顯示全部裝備", en: "Showing all equipment", es: "Mostrando todo el equipo", "pt-BR": "Mostrando todo o equipamento" },
    farmNoMissing: { "zh-TW": "這個分類沒有缺少的項目。", en: "You already have everything in this tab.", es: "En esta pestaña no te falta nada.", "pt-BR": "Nesta aba não falta nada." },
    farmNoneMissingHint: { "zh-TW": "沒有缺少的裝備，請關閉「缺少的裝備」選項", en: "You already have all gear. Turn off “Missing gear” to see everything.", es: "Ya tienes todo el equipo. Desactiva «Equipo que te falta» para verlo todo.", "pt-BR": "Você já tem todo o equipamento. Desative “Equipamento que falta” para ver tudo." },
    farmGot: { "zh-TW": "已刷出", en: "Found", es: "Conseguido", "pt-BR": "Obtido" },
    farmAllGot: { "zh-TW": "所需物品已刷出，已停止自動進入。", en: "The targeted drop was found. Auto-enter has stopped.", es: "Ya tienes el objetivo; no se volverá a entrar.", "pt-BR": "O alvo saiu; a entrada automática parou." },
    farmNone: { "zh-TW": "請先點選裝備、卡片或寵物，再按新增。", en: "Tap a piece of gear, a card, or a pet, then press Add first.", es: "Toca primero un equipo, una carta o una mascota y pulsa Añadir.", "pt-BR": "Toque primeiro um equipamento, uma carta ou um pet e pressione Adicionar." },
    farmLocked: { "zh-TW": "此關卡尚未解鎖或尚未推出。", en: "This stage is locked or not available yet.", es: "Este escenario está bloqueado o aún no está disponible.", "pt-BR": "Este estágio está bloqueado ou ainda não está disponível." },
    farmNoStage: { "zh-TW": "目前缺少的目標沒有可刷的關卡。", en: "None of the remaining targets has a farmable stage.", es: "Los objetivos pendientes no tienen un escenario disponible.", "pt-BR": "Os alvos restantes não têm um estágio disponível." },
    farmEvo: { "zh-TW": "此寵物需進化取得，無法在野外刷蛋。", en: "This pet is obtained by evolution and cannot be farmed in the field.", es: "Esta mascota se obtiene por evolución y no se puede recolectar en el campo.", "pt-BR": "Este pet é obtido por evolução e não pode ser farmado no campo." },
    minQuality: { "zh-TW": "最低品質", en: "Min. quality", es: "Calidad mín.", "pt-BR": "Qualidade mín." },
    affixes: { "zh-TW": "所需詞條", en: "Required affixes", es: "Atributos requeridos", "pt-BR": "Afixos necessários" },
    add: { "zh-TW": "新增", en: "Add", es: "Añadir", "pt-BR": "Adicionar" },
    farmTarget: { "zh-TW": "刷取目標", en: "Farm target", es: "Objetivo", "pt-BR": "Alvo" },
    farmShowing: { "zh-TW": "目前顯示此關卡會出現的項目", en: "Showing drops from this stage", es: "Mostrando lo que sale en este escenario", "pt-BR": "Mostrando o que cai neste estágio" },
    farmStageEmpty: { "zh-TW": "此關卡沒有可刷的項目。", en: "Nothing to farm in this stage.", es: "En este escenario no hay nada que recolectar.", "pt-BR": "Neste estágio não há o que farmar." },
    farmNoTarget: { "zh-TW": "尚未指定刷取目標", en: "No farm target yet", es: "Aún no hay un objetivo", "pt-BR": "Ainda não há um alvo" },
    cancel: { "zh-TW": "取消", en: "Cancel", es: "Cancelar", "pt-BR": "Cancelar" },
    confirm: { "zh-TW": "確定", en: "OK", es: "Aceptar", "pt-BR": "OK" },
    noticeTitle: { "zh-TW": "提示", en: "Notice", es: "Aviso", "pt-BR": "Aviso" },
    partyTowerBlocked: { "zh-TW": "多人組隊、魔物終結塔不能使用「提前規劃」", en: "Advance planning cannot be used in multiplayer party or Monster Tower.", es: "No se puede usar «Plan anticipado» en grupo multijugador ni en la Torre de monstruos.", "pt-BR": "Não é possível usar «Planejamento antecipado» em grupo multiplayer ou Torre de monstros." },
    partyBlocked: { "zh-TW": "多人組隊、魔物終結塔不能使用「提前規劃」", en: "Advance planning cannot be used in multiplayer party or Monster Tower.", es: "No se puede usar «Plan anticipado» en grupo multijugador ni en la Torre de monstruos.", "pt-BR": "Não é possível usar «Planejamento antecipado» em grupo multiplayer ou Torre de monstros." },
    towerBlocked: { "zh-TW": "多人組隊、魔物終結塔不能使用「提前規劃」", en: "Advance planning cannot be used in multiplayer party or Monster Tower.", es: "No se puede usar «Plan anticipado» en grupo multijugador ni en la Torre de monstruos.", "pt-BR": "Não é possível usar «Planejamento antecipado» em grupo multiplayer ou Torre de monstros." },
    moveDodgeMob: { "zh-TW": "閃避普通怪攻擊", en: "Dodge normal monster attacks", es: "Esquivar ataques normales", "pt-BR": "Desviar de ataques normais" },
    moveDodgeBoss: { "zh-TW": "閃避Boss攻擊", en: "Dodge Boss attacks", es: "Esquivar ataques de Jefe", "pt-BR": "Desviar de ataques de Chefe" },
    movePickup: { "zh-TW": "撿經驗、金幣、磁力和箱子", en: "Pick up EXP, Zeny, Magnet & Chests", es: "Recoger EXP, Zeny, Imán y Cofres", "pt-BR": "Coletar EXP, Zeny, Ímã e Baús" },
    exileMax: { "zh-TW": "放逐最多只能選取兩個", en: "Banish allows at most two selections", es: "Banish permite como máximo dos selecciones", "pt-BR": "Banish permite no máximo duas seleções" },
    exileMaxSkills: { "zh-TW": "技能最多只能選取兩個放逐", en: "Skills: at most two can be banished", es: "Habilidades: como máximo dos para Banish", "pt-BR": "Habilidades: no máximo duas para Banish" },
    exileMaxItems: { "zh-TW": "道具最多只能選取兩個放逐", en: "Items: at most two can be banished", es: "Objetos: como máximo dos para Banish", "pt-BR": "Itens: no máximo dois para Banish" },
    focusMax: { "zh-TW": "專注最多只能選取兩個", en: "Focus allows at most two selections", es: "Focus permite como máximo dos selecciones", "pt-BR": "Focus permite no máximo duas seleções" },
    headUpper: { "zh-TW": "上頭", en: "Upper", es: "Superior", "pt-BR": "Superior" },
    headMid: { "zh-TW": "中頭", en: "Middle", es: "Medio", "pt-BR": "Meio" },
    headLower: { "zh-TW": "下頭", en: "Lower", es: "Inferior", "pt-BR": "Inferior" },
    basicOrderLabel: {
      "zh-TW": "普通攻擊在選擇第一技能X次後的優先次序是？",
      en: "Priority order of Basic Attack after picking the 1st skill X times?",
      es: "¿Orden de prioridad del ataque básico tras elegir la 1.ª habilidad X veces?",
      "pt-BR": "Ordem de prioridade do ataque básico após escolher a 1.ª habilidade X vezes?",
    },
    basicOrderLast: { "zh-TW": "最後", en: "Last", es: "Último", "pt-BR": "Último" },
    planNeedJobLv: { "zh-TW": "角色列表裡沒有角色達到職業等級50\n請提升職業等級至50級再來使用", en: "No character in your list has reached Job Lv 50.\nRaise a character to Job Lv 50 to use this.", es: "Ningún personaje de tu lista ha alcanzado Job Lv 50.\nSube a Job Lv 50 para usar esto.", "pt-BR": "Nenhum personagem da lista chegou ao Nv de Classe 50.\nSuba um personagem ao Nv 50 para usar." },
    farmNext: { "zh-TW": "{n}秒後開始下一場", en: "Next run starts in {n}s", es: "La siguiente partida empieza en {n} s", "pt-BR": "A próxima partida começa em {n} s" },
  };
  const L = (k) => (COPY[k] && (COPY[k][lang] || COPY[k].en || COPY[k]["zh-TW"])) || k;
  const tUI = (es) => (DATA.i18n.ui[es] && DATA.i18n.ui[es][lang]) || es;
  function tAspect(id, skillId) {
    if (id && String(id).startsWith("effect:")) {
      const key = String(id).slice(7);
      const e = skillEffectsOf(skillId).find((x) => x.id === key);
      if (e && e.names) return e.names[lang] || e.names.en || e.names.es || key;
    }
    return (DATA.i18n.aspect[id] && DATA.i18n.aspect[id][lang]) || id;
  }
  const tItem = (it) => {
    if (!it) return "";
    const row = DATA.i18n.item[it.name];
    return (row && row[lang]) || it.name;
  };
  const tSlot = (id) => {
    const s = DATA.slots.find((x) => x.id === id);
    return (s && s.i18n && s.i18n[lang]) || (s && s.name) || id;
  };
  const tName = (en) => {
    if (!en) return "";
    if (lang === "en") return en;
    if (lang === "zh-TW") return DATA.namesZh[en] || en;
    return en;
  };

  function JOB_ICON(id, gender) {
    if (id === "bard" && gender === "f") return ICON("job_dancer");
    const job = JOBS[id];
    if (SECOND.has(id) || id === "bard") return ICON(`job_${id}`);
    return ICON((DATA.skills[job?.start] || {}).icon || `job_${id}`);
  }

  function jobName(id, gender) {
    const j = JOBS[id];
    if (!j) return id;
    if (id === "bard" && gender === "f") return tName(j.nameF || "Dancer");
    return tName(j.name);
  }

  function scalingLabel(job) {
    const sc = (job && job.scaling) || "magic";
    if (sc === "melee") return lang === "zh-TW" ? "近戰 · STR" : "Melee · STR";
    if (sc === "ranged") return lang === "zh-TW" ? "遠程 · DEX" : "Ranged · DEX";
    return lang === "zh-TW" ? "魔法 · INT" : "Magic · INT";
  }

  function jobNameList(id) {
    const j = JOBS[id];
    const names = new Set();
    if (j) {
      names.add(j.name);
      names.add(j.name.toLowerCase());
      if (j.nameF) names.add(j.nameF);
      const zh = DATA.namesZh[j.name];
      const zhF = j.nameF && DATA.namesZh[j.nameF];
      if (zh) names.add(zh);
      if (zhF) names.add(zhF);
    }
    for (const a of DATA.jobAliases[id] || []) names.add(a);
    return names;
  }

  const nameToJob = new Map();
  for (const j of DATA.jobs) {
    for (const n of jobNameList(j.id)) {
      nameToJob.set(n, j.id);
      nameToJob.set(String(n).toLowerCase(), j.id);
    }
  }

  function emptyChest() {
    const o = {};
    for (const s of SLOTS) o[s] = [];
    return o;
  }

  function normalizeBasicOrder(v) {
    return v === "2" || v === "3" || v === "4" || v === "last" ? v : "last";
  }

  function defaultPlan(jobId) {
    const defaultSkills = [];
    try {
      if (typeof jobSkills === "function") {
        const { first } = jobSkills(jobId);
        if (Array.isArray(first) && first.length) {
          defaultSkills.push(...first.slice(0, 4));
        }
      }
    } catch (_) {}
    return {
      skills: defaultSkills,
      skillAspects: {},
      chest: emptyChest(),
      skillDeity: null,
      rotateEvery: 5,
      basicOn: false,
      basicOrder: "last",
      perks: defaultPerks(),
    };
  }

  function defaultPerks() {
    return {
      skills: { rerollAll: true, rerollCard: true, exileBasic: false, focusBasic: false, exile: [], focus: [] },
      chest: { rerollAll: true, rerollCard: true, exile: [], focus: [] },
    };
  }

  function jobPerkSkills(jobId) {
    const { first, second } = jobSkills(jobId);
    return [...first, ...second].filter((id) => DATA.skills[id] && !String(id).startsWith("atk_"));
  }

  function normalizePerks(p, jobId) {
    const d = defaultPerks();
    const src = p && p.perks && typeof p.perks === "object" ? p.perks : null;
    const skills = src && src.skills && typeof src.skills === "object" ? src.skills : {};
    const chest = src && src.chest && typeof src.chest === "object" ? src.chest : {};
    const allow = new Set(jobPerkSkills(jobId));
    const sk = {
      rerollAll: skills.rerollAll !== false,
      rerollCard: skills.rerollCard !== false,
      exileBasic: skills.exileBasic === true,
      focusBasic: skills.focusBasic === true,
      // only keep explicitly stored lists — never invent a default selected skill
      exile: Array.isArray(skills.exile) ? skills.exile.filter((id) => allow.has(id)) : [],
      focus: Array.isArray(skills.focus) ? skills.focus.filter((id) => allow.has(id)) : [],
    };
    sk.focus = sk.focus.filter((id) => !sk.exile.includes(id));
    if (sk.exileBasic) sk.focusBasic = false;
    const runIds = new Set((DATA.runItems || []).map((it) => it.id));
    const deityIds = new Set(jobPerkSkills(jobId));
    const okChest = (id) => runIds.has(id) || deityIds.has(id);
    const ch = {
      rerollAll: chest.rerollAll !== false,
      rerollCard: chest.rerollCard !== false,
      exile: Array.isArray(chest.exile) ? chest.exile.filter(okChest) : [],
      focus: Array.isArray(chest.focus) ? chest.focus.filter(okChest) : [],
    };
    ch.focus = ch.focus.filter((id) => !ch.exile.includes(id));
    p.perks = { skills: sk, chest: ch };
    return p.perks;
  }

  function perkOf(jobId, kind) {
    const plan = planOf(jobId);
    return kind === "chest" ? plan.perks.chest : plan.perks.skills;
  }

  function migratePlan(p, jobId) {
    if (!p || typeof p !== "object" || Array.isArray(p)) {
      const d = defaultPlan(jobId);
      if (Array.isArray(p)) d.skills = p.slice();
      return d;
    }
    const out = defaultPlan(jobId);
    if (Array.isArray(p.skills)) out.skills = p.skills.slice();
    out.skillAspects = p.skillAspects && typeof p.skillAspects === "object" ? p.skillAspects : {};
    out.chest = emptyChest();
    if (p.chest && typeof p.chest === "object") {
      for (const s of SLOTS) if (Array.isArray(p.chest[s])) out.chest[s] = p.chest[s].slice();
    }
    out.skillDeity = typeof p.skillDeity === "string" ? p.skillDeity : null;
    const rot = Number(p.rotateEvery);
    out.rotateEvery = Number.isFinite(rot) && rot >= 1 ? Math.min(99, Math.round(rot)) : 5;
    out.basicOn = p.basicOn === true;
    out.basicOrder = normalizeBasicOrder(p.basicOrder);
    if (p.perks && typeof p.perks === "object") out.perks = p.perks;
    // legacy single exileSkill is ignored so plans start with no exile selection
    out.exileSkill = null;
    out.exileBasic = false;
    normalizePerks(out, jobId);
    // keep old global aspects as a seed when a skill popup is first opened
    if (Array.isArray(p.aspects)) out._legacyAspects = p.aspects.slice();
    if (Array.isArray(p.aspectOff)) out._legacyOff = p.aspectOff.slice();
    return out;
  }

  function loadStore() {
    let raw = null;
    try { raw = JSON.parse(localStorage.getItem(STORE_KEY) || "null"); } catch (_) {}
    if (!raw) {
      try { raw = JSON.parse(localStorage.getItem(STORE_OLD) || "null"); } catch (_) {}
    }
    const st = {
      auto: true,
      autoMove: true,
      moveOpts: { dodgeMob: true, dodgeBoss: true, pickup: true },
      job: null,
      plans: {},
      gender: "m",
      farm: defaultFarm(),
      perksSchema: 2,
      loadoutSchema: 2,
    };
    if (raw && typeof raw === "object") {
      if (typeof raw.auto === "boolean") st.auto = raw.auto;
      if (typeof raw.autoMove === "boolean") st.autoMove = raw.autoMove;
      if (raw.moveOpts && typeof raw.moveOpts === "object") {
        st.moveOpts = {
          dodgeMob: raw.moveOpts.dodgeMob !== false,
          dodgeBoss: raw.moveOpts.dodgeBoss !== false,
          pickup: raw.moveOpts.pickup !== false,
        };
      }
      if (raw.job) st.job = raw.job;
      if (raw.gender === "f" || raw.gender === "m") st.gender = raw.gender;
      if (raw.plans && typeof raw.plans === "object") {
        for (const [k, v] of Object.entries(raw.plans)) st.plans[k] = migratePlan(v, k);
      }
      st.farm = migrateFarm(raw.farm);
      // 1.3.0: drop legacy auto-seeded skill exile (old exileSkill / default one-skill pick)
      if (raw.perksSchema !== 2) {
        for (const p of Object.values(st.plans)) {
          if (!p || !p.perks || !p.perks.skills) continue;
          p.perks.skills.exile = [];
          p.perks.skills.exileBasic = false;
          p.exileSkill = null;
        }
      }
      st.perksSchema = 2;
      // 1.3.0: drop legacy default loadout that only had the job start skill
      if (raw.loadoutSchema !== 2) {
        for (const [jobId, p] of Object.entries(st.plans)) {
          if (!p || !Array.isArray(p.skills)) continue;
          const start = JOBS[jobId] && JOBS[jobId].start;
          // old defaultPlan always seeded [start]; treat single start-only as unset
          if (start && p.skills.length === 1 && p.skills[0] === start) {
            p.skills = [];
          }
          // drop invalid / basic-attack ids (isBasicSkillId may not exist yet at load time)
          p.skills = p.skills.filter((id) => id && DATA.skills[id] && id !== "basicAttack" && !String(id).startsWith("atk_"));
        }
      }
      st.loadoutSchema = 2;
    }
    return st;
  }

  function saveStore() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(store)); } catch (_) {}
  }

  let store = loadStore();
  function planOf(jobId) {
    if (!jobId || !JOBS[jobId]) return defaultPlan("swordsman");
    if (!store.plans[jobId]) store.plans[jobId] = defaultPlan(jobId);
    const p = store.plans[jobId];
    if (!Array.isArray(p.skills)) p.skills = [];
    if (!p.skillAspects || typeof p.skillAspects !== "object") p.skillAspects = {};
    if (!p.chest) p.chest = emptyChest();
    for (const s of SLOTS) if (!Array.isArray(p.chest[s])) p.chest[s] = [];
    if (typeof p.skillDeity !== "string") p.skillDeity = null;
    if (typeof p.basicOn !== "boolean") p.basicOn = false;
    p.basicOrder = normalizeBasicOrder(p.basicOrder);
    const rot = Number(p.rotateEvery);
    p.rotateEvery = Number.isFinite(rot) && rot >= 1 ? Math.min(99, Math.round(rot)) : 5;
    normalizePerks(p, jobId);
    return p;
  }

  function skillAspectsOf(jobId, skillId) {
    const plan = planOf(jobId);
    const sk = DATA.skills[skillId];
    const typ = sk && DATA.types[sk.type];
    const avail = availableAspects(skillId);
    let cfg = plan.skillAspects[skillId];
    if (!cfg) {
      const legacy = isBasicSkillId(skillId) ? avail : (plan._legacyAspects || avail);
      const off = isBasicSkillId(skillId) ? [] : (plan._legacyOff || []);
      const ordered = [];
      for (const a of legacy) if (avail.includes(a) && !ordered.includes(a)) ordered.push(a);
      for (const a of avail) if (!ordered.includes(a)) ordered.push(a);
      cfg = {
        aspects: ordered,
        aspectOff: off.filter((a) => avail.includes(a)),
        rotateEvery: 5,
      };
      plan.skillAspects[skillId] = cfg;
    }
    if (!Array.isArray(cfg.aspects)) cfg.aspects = avail.slice();
    if (!Array.isArray(cfg.aspectOff)) cfg.aspectOff = [];
    const n = Number(cfg.rotateEvery);
    cfg.rotateEvery = Number.isFinite(n) && n >= 1 ? Math.round(n) : 5;
    return cfg;
  }

  function enabledAspects(cfg) {
    return (cfg.aspects || []).filter((a) => !cfg.aspectOff.includes(a));
  }

  function parseStore(raw) {
    if (!raw) return null;
    if (typeof raw === "object") return raw;
    try { return JSON.parse(raw); } catch (_) { return null; }
  }
  function gameStoreGet(baseKey) {
    const suffix = String(baseKey).replace(/^ro-survivors\./, "");
    const fromCloud = parseStore(cloudDocs[suffix]);
    if (fromCloud) return fromCloud;
    try {
      for (const sk of ["ro-survivors-session", "ro-survivors-guest-session"]) {
        const a = JSON.parse(localStorage.getItem(sk) || "null");
        if (a && a.id != null) {
          const v = parseStore(localStorage.getItem("ro-survivors.acct." + a.id + "." + suffix));
          if (v) return v;
        }
      }
    } catch (_) {}
    try { return parseStore(localStorage.getItem(baseKey)); } catch (_) { return null; }
  }
  function chars() {
    try {
      const a = gameStoreGet("ro-survivors.characters.v1") || [];
      return Array.isArray(a) ? a.filter((c) => c && c.job) : [];
    } catch (_) {
      return [];
    }
  }
  const PLAN_MIN_JOB_LV = 1; // Custom: Unlocked for Lv 1
  function charJobLevel(ch) {
    const n = Number(ch && ch.jobLevel);
    return Number.isFinite(n) ? n : 0;
  }
  function isSecondJobChar(ch) {
    if (!ch) return false;
    const job = String(ch.job || "");
    const promo = String(ch.promotion || ch.secondJob || "");
    if (SECOND.has(job) || (promo && SECOND.has(promo))) return true;
    const jInfo = JOBS[job];
    if (jInfo && (jInfo.tier === "second" || jInfo.rank === 2)) return true;
    return false;
  }
  function planUnlocked() {
    // Custom: Unlocked for all characters from Lv 1 immediately
    return true;
  }

  function isOverlayVisible(id) {
    const el = document.getElementById(id);
    if (!el || el.classList.contains("hidden")) return false;
    if (el.style && el.style.display === "none") return false;
    return true;
  }

  function isResetScreen() {
    return isOverlayVisible("splash") || isOverlayVisible("charselect") || isOverlayVisible("charcreate");
  }

  function isLobbyScreen() {
    if (!document.body || !document.body.classList.contains("in-lobby")) return false;
    if (isResetScreen()) return false;
    return true;
  }

  function isCombatActive() {
    if (!combatGame) return false;
    if (isResetScreen() || isLobbyScreen()) return false;
    const st = combatGame.state;
    if (st && st !== "playing" && st !== "paused" && st !== "levelup" && st !== "chest") return false;
    const stageEl = document.getElementById("stage");
    const hudEl = document.getElementById("hud");
    if (hudEl && hudEl.classList.contains("hidden") && (!stageEl || stageEl.classList.contains("hidden"))) return false;
    return true;
  }

  function clearStaleCombatGame() {
    if (!combatGame) return;
    if (isResetScreen() || isLobbyScreen()) {
      pendingGames.delete(combatGame);
      combatGame = null;
      resetRotation();
      lastSteer = { x: 0, y: 0, t: 0, kind: "" };
      stickPickup = null;
      lowHpDodge = false;
      dodgeStick = { x: 0, y: 0, until: 0, mode: "" };
    }
  }

  let pickedCharHint = null; // { name, job, gender }

  function noteCharSelectNode(node) {
    if (!node || !node.closest) return;
    const cs = node.closest("#charselect");
    if (!cs) return;
    const card = node.closest(".char-card, .cs-card, [data-char], [data-id], button") || node;
    const list = chars();
    const text = (card.textContent || "").trim();
    const dataId = card.getAttribute && (card.getAttribute("data-id") || card.getAttribute("data-char") || card.getAttribute("data-idx"));
    let matchedChar = null;
    if (dataId != null && dataId !== "") {
      matchedChar = list.find((c, idx) => String(c.id) === String(dataId) || String(idx) === String(dataId)) || null;
    }
    if (!matchedChar && text) {
      const lines = text.split(/\n+/).map((s) => s.trim()).filter(Boolean);
      for (const ln of lines) {
        const hit = list.find((c) => c && c.name === ln);
        if (hit) { matchedChar = hit; break; }
      }
      if (!matchedChar) {
        matchedChar = list.find((c) => c && c.name && text.includes(c.name)) || null;
      }
    }
    if (matchedChar) {
      const rj = resolveCharJob(matchedChar);
      if (rj) {
        pickedCharHint = { name: matchedChar.name || "", job: rj.raw, gender: rj.gender };
        manualJobOverride = false;
        return;
      }
    }
    if (text) {
      const lines = text.split(/\n+/).map((s) => s.trim()).filter(Boolean);
      for (const ln of lines) {
        const jid = nameToJob.get(ln) || nameToJob.get(ln.toLowerCase());
        if (jid && JOBS[jid]) {
          let gender = "m";
          if (ln === tName("Dancer") || ln === "Dancer" || ln === "舞孃") gender = "f";
          pickedCharHint = { name: lines[0] || "", job: jid, gender };
          manualJobOverride = false;
          return;
        }
      }
    }
  }

  function scanSelectedCharCard() {
    const cs = document.getElementById("charselect");
    if (!cs || cs.classList.contains("hidden")) return;
    const sel = cs.querySelector(".char-card.sel, .char-card.selected, .char-card.active, .cs-card.sel, .cs-card.selected, [data-char].sel, [data-char].selected");
    if (sel) noteCharSelectNode(sel);
  }

  function activeCharFromSave() {
    const list = chars();
    if (!list.length) return null;
    const acc = gameStoreGet("ro-survivors.account.v1") || {};
    const activeId = acc.activeCharId ?? acc.selectedCharId ?? acc.charId ?? acc.currentCharId ?? acc.lastCharId ?? acc.active ?? acc.selected;
    if (activeId != null && activeId !== "") {
      const byId = list.find((c) => c && (c.id === activeId || String(c.id) === String(activeId)));
      if (byId) return byId;
      const idx = Number(activeId);
      if (Number.isInteger(idx) && idx >= 0 && idx < list.length && list[idx]) return list[idx];
    }
    const selfName = ((document.querySelector("#lobby-labels .lobby-name.self") || {}).textContent || "").trim();
    if (selfName) {
      const byName = list.find((c) => c && c.name === selfName);
      if (byName) return byName;
    }
    const pl = (typeof lobbyPlaza === "function" ? lobbyPlaza() : null) || livePlaza || lobbyGame;
    const g = combatGame || pl;
    const pName = g && g.player && (g.player.name || g.player.charName);
    if (pName) {
      const byPlayer = list.find((c) => c && c.name === pName);
      if (byPlayer) return byPlayer;
    }
    if (pickedCharHint && pickedCharHint.name) {
      const byHint = list.find((c) => c && c.name === pickedCharHint.name);
      if (byHint) return byHint;
    }
    return list[list.length - 1];
  }

  function resolveCharJob(ch) {
    if (!ch) return null;
    const rawJob = ch.promotion || ch.job;
    if (!rawJob || !JOBS[rawJob]) return null;
    return {
      job: rawJob,
      gender: ch.gender === "f" ? "f" : "m",
      raw: rawJob,
    };
  }

  function jobFromGameObj(g) {
    if (!g || typeof g !== "object") return null;
    const candidates = [
      g.classDef && (g.classDef.id || g.classDef.job),
      g.promotion,
      g.job,
      g.classId,
      g.player && (g.player.promotion || g.player.job || g.player.classId || (g.player.classDef && (g.player.classDef.id || g.player.classDef.job))),
      g.char && (g.char.promotion || g.char.job),
      g.character && (g.character.promotion || g.character.job),
    ];
    for (const cid of candidates) {
      if (cid && JOBS[cid]) {
        const ch = activeCharFromSave();
        const gender = (g.player && (g.player.gender === "f" || g.player.gender === "m"))
          ? g.player.gender
          : ((ch && ch.gender === "f") ? "f" : (store.gender || "m"));
        return { job: cid, gender, raw: cid };
      }
    }
    return null;
  }

  function detectJob() {
    lang = gameLang();
    clearStaleCombatGame();
    if (isCombatActive() && combatGame) {
      const fromCombat = jobFromGameObj(combatGame);
      if (fromCombat) return fromCombat;
    }
    const pl = (typeof lobbyPlaza === "function" ? lobbyPlaza() : null) || livePlaza || lobbyGame;
    if (pl && lobbyIsLive(pl)) {
      const fromPlaza = jobFromGameObj(pl);
      if (fromPlaza) return fromPlaza;
    }
    if (!isLobbyScreen()) {
      for (const elId of ["hud-job", "cp-job", "hud-name"]) {
        const txt = (document.getElementById(elId)?.textContent || "").trim();
        if (!txt) continue;
        const id = nameToJob.get(txt) || nameToJob.get(txt.toLowerCase());
        if (id && JOBS[id]) {
          let gender = store.gender || "m";
          if (txt === tName("Dancer") || txt === "Dancer" || txt === "舞孃") gender = "f";
          if (txt === tName("Bard") || txt === "Bard" || txt === "吟遊詩人") gender = "m";
          return { job: id, gender, raw: id };
        }
      }
    }
    const activeChar = activeCharFromSave();
    const resolved = resolveCharJob(activeChar);
    if (resolved) return resolved;
    if (pickedCharHint && pickedCharHint.job && JOBS[pickedCharHint.job]) {
      return { job: pickedCharHint.job, gender: pickedCharHint.gender || "m", raw: pickedCharHint.job };
    }
    if (store.job && JOBS[store.job]) return { job: store.job, gender: store.gender || "m", raw: store.job };
    return { job: null, gender: "m", raw: null };
  }

  let wasOnResetScreen = false;
  let manualJobOverride = false;

  function resetJobSelection() {
    clearStaleCombatGame();
    jobLocked = false;
    manualJobOverride = false;
    if (!resetScreenManualPick) {
      currentJob = null;
      if (store.job !== null) {
        store.job = null;
        saveStore();
      }
    }
  }

  function syncJobFromLobby() {
    clearStaleCombatGame();
    if (isResetScreen()) {
      scanSelectedCharCard();
      if (!wasOnResetScreen) {
        wasOnResetScreen = true;
        resetScreenManualPick = false;
        manualJobOverride = false;
        pickedCharHint = null;
      }
      resetJobSelection();
      return;
    }
    wasOnResetScreen = false;

    if (!isLobbyScreen() && !isCombatActive()) return;
    resetScreenManualPick = false;

    // If user manually picked a job in Plan Ahead during this lobby/run session, keep it
    if (manualJobOverride && currentJob && JOBS[currentJob]) {
      return;
    }

    lang = gameLang();
    const det = detectJob();
    const resolvedId = det && det.raw && JOBS[det.raw] ? det.raw : null;
    const gender = (det && det.gender) || store.gender || "m";

    if (!resolvedId) return;

    const changed = currentJob !== resolvedId || currentGender !== gender || store.job !== resolvedId;
    currentJob = resolvedId;
    currentGender = gender;
    store.job = resolvedId;
    store.gender = gender;
    jobLocked = true;
    if (changed) {
      saveStore();
      const ov = document.getElementById("ros-plan-ov");
      if (ov && !ov.classList.contains("hidden") && view === "plan") {
        try { renderWindow(); } catch (_) {}
      }
    }
  }

  const INFUSE_ELEM = ["fire", "water", "wind"];
  const INFUSE_TALENTS = ["fire_infusion", "water_infusion", "wind_infusion"];
  const INFUSE_ICONS = { fire: "so_fire_insignia", water: "so_water_insignia", wind: "so_wind_insignia" };

  function accountInventory() {
    const a = gameStoreGet("ro-survivors.account.v1");
    if (a && Array.isArray(a.inventory)) return a.inventory;
    return [];
  }
  function charInventory(ch) {
    if (ch && Array.isArray(ch.inventory) && ch.inventory.length) return ch.inventory;
    return accountInventory();
  }
  function jobsOfChar(ch) {
    const ids = new Set();
    for (const id of [ch && ch.job, ch && ch.promotion]) {
      if (!id) continue;
      ids.add(id);
      ids.add(parentFirstJob(id));
    }
    return ids;
  }
  function charForPlan() {
    const list = chars();
    if (!list.length) return null;
    const name = ((document.querySelector("#lobby-labels .lobby-name.self") || {}).textContent || "").trim();
    const byName = name ? list.find((c) => c.name === name) : null;
    const job = currentJob;
    const parent = parentFirstJob(job);
    const match = (c) => {
      const ids = jobsOfChar(c);
      return ids.has(job) || ids.has(parent);
    };
    if (byName && match(byName)) return byName;
    const same = list.filter(match);
    if (same.length) return same[same.length - 1];
    return byName || null;
  }
  function equippedWeaponId(ch) {
    if (!ch || !ch.equipped) return null;
    const uid = ch.equipped.weapon;
    if (!uid) return null;
    const it = charInventory(ch).find((x) => x && x.uid === uid);
    return it && it.itemId != null ? it.itemId : null;
  }
  function infuseIconFromTalents(talents) {
    if (!talents || typeof talents !== "object") return null;
    for (let i = 0; i < INFUSE_TALENTS.length; i++) {
      if ((talents[INFUSE_TALENTS[i]] || 0) > 0) return ICON(INFUSE_ICONS[INFUSE_ELEM[i]]);
    }
    return null;
  }
  function infuseIconFromMask(mask) {
    const n = Number(mask) || 0;
    if (!n) return null;
    for (let i = 0; i < INFUSE_ELEM.length; i++) {
      if (n & (1 << i)) return ICON(INFUSE_ICONS[INFUSE_ELEM[i]]);
    }
    return null;
  }
  function jobStartIcon(jobId) {
    const job = JOBS[jobId] || JOBS[currentJob];
    const sk = job && DATA.skills[job.start];
    return sk ? ICON(sk.icon) : ICON("atk_fist");
  }
  function runMatchesPlan(g) {
    const id = g && g.classDef && (g.classDef.id || g.classDef.job);
    if (!id) return true;
    return id === currentJob || parentFirstJob(id) === parentFirstJob(currentJob);
  }
  function basicAttackIcon() {
    const g = combatGame;
    if (g && runMatchesPlan(g) && (g.basicAttack || g.loadout || (g.stats && g.stats.infuse))) {
      if (g.stats && g.stats.infuse) {
        const ic = infuseIconFromMask(g.stats.infuse);
        if (ic) return ic;
      }
      const w = g.loadout && g.loadout.weapon;
      const id = w && (w.itemId != null ? w.itemId : w.id);
      if (id != null) return `/assets/items/${id}.png`;
      return jobStartIcon(currentJob);
    }
    const ch = charForPlan();
    if (ch) {
      const ic = infuseIconFromTalents(ch.talents);
      if (ic) return ic;
      const id = equippedWeaponId(ch);
      if (id != null) return `/assets/items/${id}.png`;
    }
    return jobStartIcon(currentJob);
  }
  function syncBasicAttackIcon() {
    const ov = document.getElementById("ros-plan-ov");
    if (!ov || ov.classList.contains("hidden")) return;
    const img = ov.querySelector(".ros-basic-chip img");
    if (!img) return;
    const next = basicAttackIcon();
    if (next && img.getAttribute("src") !== next) img.src = next;
  }

  function parentFirstJob(jobId) {
    const j = JOBS[jobId];
    if (!SECOND.has(jobId)) return jobId;
    const start = j && j.start;
    if (start) {
      for (const [fid, skills] of Object.entries(DATA.firstSkills)) {
        if (skills.includes(start)) return fid;
      }
      for (const fj of DATA.jobs) {
        if (!SECOND.has(fj.id) && fj.start === start) return fj.id;
      }
    }
    return jobId;
  }

  function jobSkills(jobId) {
    const parent = parentFirstJob(jobId);
    const first = DATA.firstSkills[parent] || DATA.firstSkills[jobId] || [];
    const second = SECOND.has(jobId) ? (DATA.secondSkills[jobId] || []) : [];
    return { first, second };
  }

  function jobSkillDeities(jobId) {
    const { first, second } = jobSkills(jobId);
    return [...first, ...second].filter((id) => DATA.skills[id] && !String(id).startsWith("atk_"));
  }

  function tSkillDeity(skillId) {
    const sk = DATA.skills[skillId];
    return `${tName(sk && sk.name) || skillId} Deity`;
  }

  function maxSlots(jobId) {
    return SECOND.has(jobId) ? (DATA.maxSkills.second || 5) : (DATA.maxSkills.first || 4);
  }

  /* Card wording follows game DA()/zv(), not wiki labels like Enfriamiento / Cantidad. */
  const PHRASE = {
    dmg: ["傷害", "de daño", "daño", "damage", "de dano", "dano"],
    cd: ["冷卻縮減", "冷卻", "celeridad", "haste", "aceleração", "aceleracao",
         "rapidez de casteo", "詠唱速度", "cast speed", "velocidade de conjuração",
         "enfriamiento", "cooldown", "recarga"],
    reach: ["近戰攻擊範圍", "melee reach", "alcance cuerpo a cuerpo", "alcance corpo a corpo",
            "射程", "alcance", "reach"],
    area: ["濺射", "de salpicadura", "splash", "dano em área", "de área", "área", "area", "範圍"],
    duration: ["持續時間", "de duración", "duration", "de duração", "duração", "duración"],
    pierce: ["貫穿機率", "pierce chance", "de perforación", "perforación", "perfuração",
             "貫穿", "pierce", "penetración", "penetração"],
    speed: ["投射物速度", "環繞速度", "projectile speed", "orbit speed",
            "velocidad de proyectil", "velocidad de giro", "velocidade do projétil", "velocidade de giro",
            "移動速度", "movement speed", "velocidad de movimiento", "velocidade de movimento",
            "速度", "velocidad", "speed", "velocidade"],
    effect: ["效果更強", "efecto más fuerte", "stronger effect", "efeito mais forte",
             "效果", "efecto", "effect", "efeito"],
  };
  const COUNT_UNITS = [
    "proyectiles", "proyectil", "projectiles", "projectile", "投射物", "projéteis", "projétil",
    "andanadas", "andanada", "volleys", "volley", "salvas", "salva",
    "flechas", "flecha", "arrows", "arrow", "支箭",
    "impactos", "impacto", "impacts", "impact", "次衝擊", "衝擊",
    "pulsos", "pulso", "pulses", "pulse", "次脈衝", "脈衝",
    "orbes", "orbe", "orbs", "orb", "顆光球", "光球",
    "celdas", "celda", "cells", "cell", "células", "célula", "celulas", "celula",
    "cargas", "carga", "charges", "charge", "次充能",
    "llamas", "llama", "flames", "flame", "火焰", "chamas", "chama",
    "rayos", "rayo", "bolts", "bolt", "relâmpagos", "relâmpago",
    "almas", "alma", "souls", "soul", "靈魂",
    "shurikens", "shuriken", "手裡劍",
    "pétalos", "pétalo", "petals", "petal", "花瓣", "pétalas", "pétala",
    "kunais", "kunai", "苦無",
    "balas", "bala", "bullets", "bullet", "子彈",
    "ráfagas", "ráfaga", "bursts", "burst", "連射", "rajadas", "rajada",
    "cantidad", "quantidade", "數量上限", "數量", "amount",
  ];
  const TARGET_UNITS = [
    "objetivos", "objetivo", "targets", "target", "alvos", "alvo", "目標數", "額外目標", "目標",
  ];
  const SHORT_COUNT = ["輪", "格", "發"];

  function norm(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }
  function hasPhrase(t, k) {
    if (!k) return false;
    if (/^[a-z]{1,2}$/.test(k)) return new RegExp(`(?:^|[^a-z])${k}(?:$|[^a-z])`, "i").test(t);
    return t.includes(k);
  }
  function hasAny(t, keys) {
    const keysN = keys.map((k) => norm(k)).sort((a, b) => b.length - a.length);
    const tn = norm(t);
    for (const k of keysN) if (hasPhrase(tn, k)) return true;
    return false;
  }
  function hasShortCount(t) {
    return /(?:^|[+\d\s])(?:輪|格|發)(?:$|[^\u4e00-\u9fff])/u.test(t) ||
           /\d+\s*(?:輪|格|發)/u.test(t);
  }
  function typeAspectsOf(skillId) {
    const sk = skillId && DATA.skills[skillId];
    const typ = sk && sk.type && DATA.types[sk.type];
    return typ && typ.aspects ? typ.aspects.slice() : null;
  }
  function skillEffectsOf(skillId) {
    const sk = skillId && DATA.skills[skillId];
    return (sk && Array.isArray(sk.effects)) ? sk.effects : [];
  }
  const BASIC_SKILL_ID = "basicAttack";
  const BASIC_ASPECTS = ["dmg", "cd", "count", "reach", "targets", "pierce", "speed", "area"];

  function isBasicSkillId(id) {
    return id === BASIC_SKILL_ID || (id && String(id).startsWith("atk_"));
  }

  function availableAspects(skillId) {
    if (isBasicSkillId(skillId)) {
      const g = combatGame;
      if (g && typeof g.skillDef === "function" && g.basicAttack) {
        try {
          const def = g.skillDef(g.basicAttack);
          const typ = def && def.type && DATA.types[def.type];
          if (typ && typ.aspects && typ.aspects.length) return typ.aspects.slice();
        } catch (_) {}
      }
      return BASIC_ASPECTS.slice();
    }
    const typ = typeAspectsOf(skillId) || [];
    return typ.concat(skillEffectsOf(skillId).map((e) => "effect:" + e.id));
  }
  function matchEffect(chunk, skillId) {
    const effs = skillEffectsOf(skillId);
    if (!effs.length) return null;
    const tn = norm(chunk).replace(/\s+/g, " ").trim();
    let best = null, bestLen = 0;
    for (const e of effs) {
      for (const lab of Object.values(e.names || {})) {
        const ln = norm(lab).trim();
        if (!ln) continue;
        if (tn === ln || tn.startsWith(ln + ":") || tn.startsWith(ln + "：") || hasPhrase(tn, ln)) {
          if (ln.length > bestLen) { best = "effect:" + e.id; bestLen = ln.length; }
        }
      }
    }
    return best;
  }

  function maskPhrases(text, phrases) {
    let s = text;
    const keys = phrases.map((k) => k).sort((a, b) => b.length - a.length);
    for (const k of keys) {
      if (!k) continue;
      const re = new RegExp(k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
      s = s.replace(re, " ");
    }
    return s;
  }

  function matchChunk(chunk, skillId) {
    const found = [];
    const typ = typeAspectsOf(skillId);

    if (hasAny(chunk, PHRASE.reach)) found.push("reach");
    if (hasAny(chunk, PHRASE.area)) {
      const reachHit = found.includes("reach") || hasAny(chunk, ["近戰攻擊範圍", "melee reach", "alcance cuerpo a cuerpo", "alcance corpo a corpo"]);
      if (!reachHit) found.push("area");
    }
    if (hasAny(chunk, PHRASE.cd)) found.push("cd");
    if (hasAny(chunk, PHRASE.dmg)) found.push("dmg");
    if (hasAny(chunk, PHRASE.duration)) found.push("duration");
    if (hasAny(chunk, PHRASE.pierce)) found.push("pierce");
    if (hasAny(chunk, PHRASE.speed)) found.push("speed");

    const rest = maskPhrases(chunk, [].concat(
      PHRASE.speed, PHRASE.reach, PHRASE.cd, PHRASE.duration, PHRASE.pierce, PHRASE.area, PHRASE.dmg
    ));
    const countHit = hasAny(rest, COUNT_UNITS) || hasShortCount(rest);
    const targetHit = hasAny(rest, TARGET_UNITS);
    if (targetHit && !countHit) {
      if (typ && typ.includes("targets")) found.push("targets");
      else if (typ && typ.includes("count") && !typ.includes("targets")) found.push("count");
      else found.push("targets");
    } else if (countHit && !targetHit) {
      found.push("count");
    } else if (countHit && targetHit) {
      if (typ && typ.includes("targets") && typ.includes("count")) found.push("targets");
      else if (typ && typ.includes("count")) found.push("count");
      else found.push("targets");
    }

    if (hasAny(chunk, PHRASE.effect)) found.push("effect");
    return [...new Set(found)];
  }

  function isDaLine(chunk) {
    return /^\s*[+\-]/.test(chunk);
  }

  function parseAspects(text, skillId, isUpgrade) {
    const raw = (text || "").trim();
    if (!raw) return [];
    const chunks = raw.split(/\s\+\s|\n+/).map((s) => s.trim()).filter(Boolean);
    const found = [];
    for (const chunk of chunks) {
      const eff = matchEffect(chunk, skillId);
      if (isDaLine(chunk)) {
        const ids = matchChunk(chunk, skillId);
        const structural = ids.filter((a) => a !== "effect");
        if (structural.length) found.push(...structural);
        else if (eff) found.push(eff);
        else found.push("effect");
      } else if (eff) {
        found.push(eff);
      } else if (isUpgrade || hasAny(chunk, PHRASE.effect)) {
        found.push("effect");
      }
    }
    return [...new Set(found)];
  }

  function skillIdFromCard(card) {
    const img = card.querySelector(".pk-art img") || card.querySelector("img");
    const src = img?.getAttribute("src") || "";
    const m = src.match(/\/icons\/([^/?#]+)\.(?:png|webp)/i);
    const icon = m ? decodeURIComponent(m[1]) : "";
    const name = (card.querySelector(".pk-name")?.textContent || "").trim();
    let found = null;
    if (icon) found = Object.values(DATA.skills).find((s) => s.icon === icon);
    if (!found && name) {
      found = Object.values(DATA.skills).find((s) => tName(s.name) === name || s.name === name || DATA.namesZh[s.name] === name);
    }
    return found ? found.id : null;
  }

  function isNewSkillCard(card) {
    const badge = (card.querySelector(".pk-badge")?.textContent || "").trim();
    const fresh = (card.querySelector(".pk-ribbon")?.textContent || "").trim();
    const skillWord = new Set(["Habilidad", "Skill", "技能", "Habilidade", tUI("Habilidad")]);
    const neu = new Set(["¡NUEVA!", "NEW!", "新！", "NOVA!", tUI("¡NUEVA!")]);
    return skillWord.has(badge) || neu.has(fresh);
  }

  function rarityOf(card) {
    const badge = (card.querySelector(".pk-badge")?.textContent || "").trim().toLowerCase();
    const table = [
      ["Legendario", "Legendaria", "Legendary", "傳說", "Lendário", "Lendária"],
      ["Épico", "Épica", "Epic", "史詩"],
      ["Raro", "Rara", "Rare", "稀有"],
      ["Poco común", "Uncommon", "優良", "Incomum"],
      ["Común", "Common", "普通", "Comum"],
    ];
    for (let i = 0; i < table.length; i++) {
      if (table[i].some((n) => n.toLowerCase() === badge)) return 4 - i;
    }
    return 0;
  }

  /* rotation: A×N, B, A×N, C, ... A×N, last, then wrap from B */
  const rotateMemo = new Map();
  function rotState(skillId) {
    if (!rotateMemo.has(skillId)) rotateMemo.set(skillId, { streak: 0, slot: 0 });
    return rotateMemo.get(skillId);
  }
  function resetRotation() { rotateMemo.clear(); }

  function dueAspect(cfg, skillId) {
    const en = enabledAspects(cfg);
    if (!en.length) return null;
    if (en.length === 1) return en[0];
    const N = loadoutRotateEvery(planOf(currentJob));
    const st = rotState(skillId);
    if (st.streak < N) return en[0];
    return en[1 + (st.slot % (en.length - 1))];
  }

  function consumeAspect(cfg, skillId, picked, exact) {
    if (!exact) return;
    const en = enabledAspects(cfg);
    if (!en.length) return;
    const N = loadoutRotateEvery(planOf(currentJob));
    const st = rotState(skillId);
    if (en.length === 1) { st.streak++; return; }
    if (picked === en[0] && st.streak < N) st.streak++;
    else if (st.streak >= N && picked === en[1 + (st.slot % (en.length - 1))]) {
      st.streak = 0;
      st.slot++;
    }
  }

  function firstNumber(text) {
    const m = String(text || "").replace(/(\d),(\d)/g, "$1.$2").match(/[+\-]?\d+(?:\.\d+)?/);
    return m ? Math.abs(parseFloat(m[0])) : 0;
  }

  function aspectValue(text, aspectId, skillId) {
    const raw = (text || "").trim();
    if (!raw || !aspectId) return 0;
    const chunks = raw.split(/\s\+\s|\n+/).map((s) => s.trim()).filter(Boolean);
    let best = 0;
    let any = false;
    for (const chunk of chunks) {
      let ids;
      if (isDaLine(chunk)) ids = matchChunk(chunk, skillId).filter((a) => a !== "effect");
      else {
        const eff = matchEffect(chunk, skillId);
        ids = eff ? [eff] : (aspectId === "effect" ? ["effect"] : []);
      }
      if (!ids.includes(aspectId)) continue;
      any = true;
      const n = firstNumber(chunk);
      if (n > best) best = n;
    }
    return any ? best : firstNumber(raw);
  }

  function scoreUpgrade(card, jobId) {
    const basic = isBasicAttackCard(card);
    const sid = basic ? BASIC_SKILL_ID : skillIdFromCard(card);
    const lis = [...card.querySelectorAll(".pk-lines li")].map((li) => li.innerText.trim()).filter(Boolean);
    const text = lis.length ? lis.join(" + ") : (card.querySelector(".pk-lines")?.innerText || card.innerText || "");
    const found = parseAspects(text, sid, true);
    if (!found.length) return null;
    if (!sid) return null;
    const cfg = skillAspectsOf(jobId, sid);
    const en = enabledAspects(cfg);
    if (!en.length) return null;
    const due = dueAspect(cfg, sid);
    const rare = rarityOf(card);
    let pick = null, priority = Infinity, exact = false;
    for (const a of found) {
      const i = en.indexOf(a);
      if (i >= 0 && i < priority) {
        priority = i;
        pick = a;
      }
    }
    if (pick == null) return null;
    if (due && pick === due) exact = true;
    const value = aspectValue(text, pick, sid);
    return { due, pick, exact, sid, rare, priority, value, basic };
  }

  function compareUpgradeScore(a, b) {
    // Returns < 0 if a is strictly better than b, > 0 if b is strictly better than a, 0 if tied
    if (a.priority !== b.priority) return a.priority - b.priority;
    if (a.value !== b.value) return b.value - a.value;
    return 0;
  }

  function itemIdFromCard(card) {
    const img = card.querySelector(".pk-art img") || card.querySelector("img");
    const src = img?.getAttribute("src") || "";
    const name = (card.querySelector(".pk-name")?.textContent || "").trim();
    let m = src.match(/\/runitems\/([^/?#]+)\.(?:png|webp)/i);
    if (m) {
      const id = decodeURIComponent(m[1]);
      if (RUN[id]) return id;
    }
    m = src.match(/\/items\/(\d+)\.(?:png|webp)/i);
    if (m) {
      const icon = Number(m[1]);
      const hit = DATA.runItems.find((it) => it.icon === icon);
      if (hit) return hit.id;
    }
    if (name) {
      const hit = DATA.runItems.find((it) => tItem(it) === name || it.name === name || (DATA.i18n.item[it.name] && Object.values(DATA.i18n.item[it.name]).includes(name)));
      if (hit) return hit.id;
    }
    m = src.match(/\/icons\/([^/?#]+)\.(?:png|webp)/i);
    if (m) {
      const icon = decodeURIComponent(m[1]);
      const hit = Object.values(DATA.skills).find((sk) => sk.icon === icon);
      if (hit) return hit.id;
    }
    if (name) {
      const base = name.replace(/(?:\s*Deity|\s*神祇|\s*Divindade)$/i, "").replace(/^(?:Deity\s+(?:de|of)\s+|神祇[：:\s]*)/i, "").trim() || name;
      const hit = Object.values(DATA.skills).find((sk) => {
        const nm = tName(sk.name);
        return nm === name || nm === base || sk.name === name || sk.name === base || sk.nameZh === name || sk.nameZh === base;
      });
      if (hit) return hit.id;
    }
    return null;
  }

  function chestKind(id) {
    const m = String(id || "").match(/^[pebdg]_(.+)$/);
    return m ? m[1] : id;
  }

  function chestLineInfo(card) {
    const lis = [...card.querySelectorAll(".pk-lines li")].map((li) => li.innerText.trim()).filter(Boolean);
    const text = lis.length ? lis.join(" + ") : ((card.querySelector(".pk-lines") && card.querySelector(".pk-lines").innerText) || "");
    return { value: firstNumber(text), unit: /[%％]/.test(text) ? "pct" : "flat" };
  }

  function scoreChest(card, jobId) {
    const id = itemIdFromCard(card);
    if (!id) return null;
    const plan = planOf(jobId);
    const info = chestLineInfo(card);
    const rare = rarityOf(card);
    if (plan.skillDeity && id === plan.skillDeity) {
      return { id, kind: "skill-deity", unit: info.unit, value: info.value, priority: -1, rare };
    }
    if (!RUN[id]) return null;
    const slot = RUN[id].slot;
    const list = plan.chest[slot] || [];
    const i = list.indexOf(id);
    if (i < 0) return null;
    return { id, kind: chestKind(id), unit: info.unit, value: info.value, priority: i, rare };
  }

  function compareChestScore(a, b) {
    // Path 2-2-1: higher priority first -> higher value first -> 0 if tied (random pick)
    if (a.priority !== b.priority) return a.priority - b.priority;
    if (a.value !== b.value) return b.value - a.value;
    return 0;
  }

  function combatCardSkillId(card, jobId) {
    if (isBasicAttackCard(card)) return planOf(jobId).basicOn ? BASIC_SKILL_ID : null;
    const sid = skillIdFromCard(card);
    return (sid && planOf(jobId).skills.includes(sid)) ? sid : null;
  }

  function chestCardHasPlannedSlot(card, jobId) {
    const id = itemIdFromCard(card);
    if (!id) return false;
    const plan = planOf(jobId);
    if (RUN[id]) {
      const slot = RUN[id].slot;
      return Array.isArray(plan.chest[slot]) && plan.chest[slot].length > 0;
    }
    return !!plan.skillDeity;
  }

  function pickRandomTie(candidates, cmpFn) {
    if (!candidates.length) return null;
    let best = [candidates[0]];
    for (let i = 1; i < candidates.length; i++) {
      const diff = cmpFn(candidates[i], best[0]);
      if (diff < 0) best = [candidates[i]];
      else if (diff === 0) best.push(candidates[i]);
    }
    return best[Math.floor(Math.random() * best.length)];
  }

  function pickBestCombatCard(cards, jobId) {
    const plan = planOf(jobId);
    const seq = loadoutSeq(jobId);
    const due = dueLoadoutSkill(jobId);
    const N = loadoutRotateEvery(plan);
    const st = skillRotState();
    const wantingSecondary = seq.length >= 2 && st.streak >= N;
    const entries = [];
    cards.forEach((c, i) => {
      const slot = c.closest(".pk-slot");
      if (slot && slot.classList.contains("asking")) return;
      const sid = combatCardSkillId(c, jobId);
      if (!sid) return;
      const basic = isBasicSkillId(sid);
      const neu = !basic && isNewSkillCard(c);
      const seqIdx = seq.indexOf(sid);
      const baseRank = seqIdx >= 0 ? seqIdx : 99;
      let effRank = baseRank;
      if (due && sid === due) {
        effRank = -1;
      } else if (wantingSecondary && seqIdx >= 1) {
        effRank = 0;
      } else if (wantingSecondary && seqIdx === 0) {
        effRank = 1;
      }
      const sc = neu ? null : scoreUpgrade(c, jobId);
      entries.push({ card: c, index: i, sid, basic, neu, baseRank, effRank, sc });
    });
    if (!entries.length) return null;

    // Path 2-1-1: cards that match 出戰技能 AND (are NEW skill cards OR have an enabled upgrade aspect in priority order)
    const qualified = entries.filter((e) => e.neu || e.sc != null);
    if (qualified.length) {
      const win = pickRandomTie(qualified, (a, b) => {
        // 1. Compare 出戰技能 rotation/priority order
        if (a.effRank !== b.effRank) return a.effRank - b.effRank;
        if (a.baseRank !== b.baseRank) return a.baseRank - b.baseRank;
        // 2. If same skill: new skill unlock vs upgrade aspect priority
        if (a.neu !== b.neu) return a.neu ? -1 : 1;
        if (a.sc && b.sc) {
          // 3. Compare enabled upgrade aspect priority order, then numeric value
          return compareUpgradeScore(a.sc, b.sc);
        }
        return 0;
      });
      return { best: win, disabledToReroll: null };
    }

    // Path 2-1-2: cards match 出戰技能, but NONE of their upgrade aspects are enabled in the skill's priority list
    const perks = perkOf(jobId, "skills");
    const topUnmatched = pickRandomTie(entries, (a, b) => {
      if (a.effRank !== b.effRank) return a.effRank - b.effRank;
      return a.baseRank - b.baseRank;
    });

    // If "重抽卡片" is enabled, try rerolling this card until an enabled upgrade aspect appears
    if (topUnmatched && perks.rerollCard !== false) {
      return { best: topUnmatched, disabledToReroll: topUnmatched.card };
    }

    // If "重抽卡片" is disabled or out of uses, pick this 出戰技能 card directly
    return { best: topUnmatched, disabledToReroll: null };
  }

  function pickIndex(cards, jobId, kind) {
    if (kind === "chest") {
      const candidates = [];
      cards.forEach((c, i) => {
        const slot = c.closest(".pk-slot");
        if (slot && slot.classList.contains("asking")) return;
        const sc = scoreChest(c, jobId);
        if (!sc) return;
        candidates.push({ ...sc, index: i });
      });
      if (!candidates.length) return { index: -1, meta: null, disabledToReroll: null };
      // Path 2-2-1: highest priority -> highest value -> random among ties
      const win = pickRandomTie(candidates, compareChestScore);
      return { index: win.index, meta: null, disabledToReroll: null };
    }
    const res = pickBestCombatCard(cards, jobId);
    if (!res) return { index: -1, meta: null, disabledToReroll: null };
    return {
      index: res.best.index,
      meta: res.best.sc || { sid: res.best.sid, pick: null, exact: false },
      disabledToReroll: res.disabledToReroll,
    };
  }

  let skillRot = { streak: 0, slot: 0, token: -1 };
  function skillRotState() {
    if (typeof lastGameToken === "number" && skillRot.token !== lastGameToken) {
      skillRot = { streak: 0, slot: 0, token: lastGameToken };
    }
    return skillRot;
  }
  function loadoutRotateEvery(plan) {
    const n = Number(plan && plan.rotateEvery);
    return Number.isFinite(n) ? Math.max(1, Math.min(99, Math.round(n))) : 5;
  }
  function loadoutSeq(jobId) {
    const plan = planOf(jobId);
    const skills = (plan.skills || []).filter((id) => DATA.skills[id] && !isBasicSkillId(id));
    if (!plan.basicOn) return skills.slice();
    const order = normalizeBasicOrder(plan.basicOrder);
    if (!skills.length) return [BASIC_SKILL_ID];
    const seq = skills.slice();
    if (order === "2") seq.splice(1, 0, BASIC_SKILL_ID);
    else if (order === "3") seq.splice(Math.min(2, seq.length), 0, BASIC_SKILL_ID);
    else if (order === "4") seq.splice(Math.min(3, seq.length), 0, BASIC_SKILL_ID);
    else seq.push(BASIC_SKILL_ID);
    return seq;
  }
  function dueLoadoutSkill(jobId) {
    const seq = loadoutSeq(jobId);
    if (!seq.length) return null;
    if (seq.length === 1) return seq[0];
    const N = loadoutRotateEvery(planOf(jobId));
    const st = skillRotState();
    if (st.streak < N) return seq[0];
    const altCount = seq.length - 1;
    return seq[1 + (st.slot % altCount)];
  }
  function consumeLoadoutSkill(jobId, pickedId) {
    const seq = loadoutSeq(jobId);
    if (!seq.length || !pickedId) return;
    const normId = isBasicSkillId(pickedId) ? BASIC_SKILL_ID : pickedId;
    const N = loadoutRotateEvery(planOf(jobId));
    const st = skillRotState();
    if (seq.length === 1) {
      if (normId === seq[0]) st.streak++;
      return;
    }
    const altCount = seq.length - 1;
    const due = st.streak < N ? seq[0] : seq[1 + (st.slot % altCount)];
    if (st.streak < N) {
      if (normId === seq[0]) st.streak++;
    } else if (normId === due) {
      st.streak = 0;
      st.slot = (st.slot + 1) % altCount;
    } else {
      const altIdx = seq.indexOf(normId);
      if (altIdx >= 1) {
        st.streak = 0;
        st.slot = altIdx % altCount;
      }
    }
  }

  let pickTimer = 0;
  let pickDueAt = 0;
  let lastPickAt = 0;

  function pickerKind(title, pickerEl) {
    const t = String(title || "").trim();
    if (t) {
      if (LEVEL_UP.has(t)) return "levelup";
      if (CHEST_TITLE.has(t)) return "chest";
      const tl = t.toLowerCase();
      if (/level\s*up|升級|升级|subiu\s*de\s*n[ií]vel|choose\s*a\s*skill|upgrade\s*a\s*skill|選擇技能|強化技能/i.test(tl)) return "levelup";
      if (/treasure\s*chest|cofre|寶箱|宝箱|ba[uú]/i.test(tl)) return "chest";
    }
    const p = pickerEl || document.getElementById("picker");
    if (p) {
      const sub = (p.querySelector("#pk-sub")?.textContent || "").trim();
      if (/選擇技能|強化技能|choose\s*a\s*skill|upgrade\s*a\s*skill|elige\s*una\s*habilidad|mejora\s*una\s*habilidad|escolha\s*uma\s*habilidade|melhore\s*uma\s*habilidade/i.test(sub)) return "levelup";
      const cards = [...p.querySelectorAll("#pk-cards .pk-card")];
      if (cards.length) {
        if (cards.some((c) => isBasicAttackCard(c) || !!skillIdFromCard(c))) return "levelup";
        if (cards.some((c) => !!itemIdFromCard(c))) return "chest";
      }
    }
    return null;
  }


  function pickerSlotsFull(picker) {
    const sock = picker && picker.querySelector("#lu-sockets");
    const text = sock && !sock.classList.contains("hidden") ? (sock.innerText || "") : "";
    const m = text.match(/(\d+)\s*\/\s*(\d+)/);
    if (m) return Number(m[1]) >= Number(m[2]);
    if (/欄位已滿|Huecos llenos|slots are full|espaços cheios/i.test(text)) return true;
    const sub = (document.getElementById("pk-sub")?.textContent || "").trim();
    if (/強化技能|Mejora una habilidad|Improve a skill|Melhore uma habilidade/.test(sub)) return true;
    if (/選擇技能|Elige una habilidad|Choose a skill|Escolha uma habilidade/.test(sub)) return false;
    return false;
  }

  function isBarFullForKind(picker, kind, jobId) {
    if (kind === "chest") {
      const sock = picker && picker.querySelector("#lu-sockets");
      const text = sock && !sock.classList.contains("hidden") ? (sock.innerText || "") : "";
      const m = text.match(/(\d+)\s*\/\s*(\d+)/);
      if (m) return Number(m[1]) >= Number(m[2]);
      if (/欄位已滿|Huecos llenos|slots are full|espaços cheios/i.test(text)) return true;

      const g = combatGame;
      if (g) {
        const ri = g.runItems || g.boons || g.items;
        if (Array.isArray(ri) && ri.length >= SLOTS.length) return true;
        if (ri && typeof ri === "object" && !Array.isArray(ri)) {
          const filled = SLOTS.filter((s) => {
            const v = ri instanceof Map ? ri.get(s) : ri[s];
            return v != null && v !== false && v !== "";
          }).length;
          if (filled >= SLOTS.length) return true;
        }
      }

      const bar = document.getElementById("runitems");
      if (bar && !bar.classList.contains("hidden")) {
        const slots = [...bar.children].filter((el) => el && el.offsetParent !== null);
        if (slots.length >= SLOTS.length) {
          const filledSlots = slots.filter((el) => !el.classList.contains("empty") && (el.querySelector("img") || (el.textContent || "").trim()));
          if (filledSlots.length >= SLOTS.length) return true;
        }
        const imgs = bar.querySelectorAll("img");
        if (imgs.length >= SLOTS.length) return true;
      }
      return false;
    }

    if (pickerSlotsFull(picker)) return true;
    const g = combatGame;
    const max = maxSlots(jobId);
    if (g && Array.isArray(g.skills)) {
      const activeCount = g.skills.filter((s) => s && !isBasicSkillId(s.id || s)).length;
      if (activeCount >= max) return true;
    }
    const sbar = document.getElementById("skillbar");
    if (sbar && !sbar.classList.contains("hidden")) {
      const slots = [...sbar.children].filter((el) => el && el.offsetParent !== null);
      if (slots.length >= max) {
        const filledSlots = slots.filter((el) => !el.classList.contains("empty") && el.querySelector("img"));
        if (filledSlots.length >= max) return true;
      }
    }
    return false;
  }

  function actText(btn) {
    return `${btn.title || ""} ${btn.textContent || ""}`;
  }

  function isRerollDeckBtn(btn) {
    const act = btn.dataset.act || "";
    const inSlot = !!btn.closest(".pk-slot");
    if (inSlot) return false;
    if (act && !act.startsWith("bar:") && !/reroll|deck|all/i.test(act)) return false;
    return /重抽全部|重新抽選|Reroll deck|Reroll all|Cambia todas las cartas|將所有卡片換成|Troca todas as cartas/i.test(actText(btn));
  }

  function isRerollCardBtn(btn) {
    const act = btn.dataset.act || "";
    if (act.startsWith("bar:")) return false;
    const t = actText(btn);
    return /重抽卡片|重抽此卡|Reroll card|Reroll slot|同一技能的不同強化|同一欄位，不同抽選|mesmo espaço|same slot|same habilidad|otra mejora/i.test(t);
  }

  function isBanishBtn(btn) {
    const act = btn.dataset.act || "";
    if (act.startsWith("bar:")) return false;
    return /放逐|排除|Banish|Exile|Desterrar|Banir/i.test(actText(btn));
  }

  function clickPkAct(root, pred) {
    const btns = [...(root.querySelectorAll("button.pk-act") || [])];
    const btn = btns.find((b) => !b.disabled && pred(b));
    if (!btn) return false;
    lastPickAt = performance.now();
    btn.click();
    return true;
  }

  function chestPriorityIds(jobId) {
    const plan = planOf(jobId);
    const ids = new Set();
    for (const slot of SLOTS) {
      for (const id of plan.chest[slot] || []) ids.add(id);
    }
    if (plan.skillDeity) ids.add(plan.skillDeity);
    return ids;
  }

  function skillCardHasEnabledAspect(card, jobId) {
    if (isBasicAttackCard(card)) {
      return !!planOf(jobId).basicOn && enabledAspects(skillAspectsOf(jobId, BASIC_SKILL_ID)).length > 0;
    }
    const sid = skillIdFromCard(card);
    if (!sid || !planOf(jobId).skills.includes(sid)) return false;
    // new skill card (no upgrade aspect yet) counts as priority
    if (isNewSkillCard(card)) return true;
    const sc = scoreUpgrade(card, jobId);
    return !!(sc && !sc.basic);
  }

  function isCombatSkillCard(card, jobId) {
    if (isBasicAttackCard(card)) return !!planOf(jobId).basicOn;
    const sid = skillIdFromCard(card);
    return !!(sid && planOf(jobId).skills.includes(sid));
  }

  function isPriorityPickCard(card, jobId, kind) {
    if (kind === "chest") {
      const id = itemIdFromCard(card);
      return !!(id && chestPriorityIds(jobId).has(id));
    }
    // skill: only if combat skill AND its upgrade aspect is prioritized (or new skill)
    return skillCardHasEnabledAspect(card, jobId);
  }

  function isRerollCardCandidate(card, jobId, kind) {
    if (kind === "chest") {
      // for chest, reroll-card is used after reroll-all exhausted; candidates are non-priority
      return !isPriorityPickCard(card, jobId, kind);
    }
    // skill: has combat skill but aspect not prioritized
    if (!isCombatSkillCard(card, jobId)) return false;
    return !skillCardHasEnabledAspect(card, jobId);
  }

  function clickRerollCardOn(card) {
    const slot = card.closest(".pk-slot");
    if (!slot || slot.classList.contains("asking")) return false;
    const btn = [...slot.querySelectorAll("button.pk-act")].find((b) => !b.disabled && isRerollCardBtn(b));
    if (!btn) return false;
    lastPickAt = performance.now();
    btn.click();
    return true;
  }

  function tryPickerReroll(picker, kind, jobId) {
    const perks = perkOf(jobId, kind === "chest" ? "chest" : "skills");
    const cards = [...picker.querySelectorAll("#pk-cards .pk-card")].filter((c) => {
      const slot = c.closest(".pk-slot");
      return !(slot && slot.classList.contains("asking"));
    });
    if (!cards.length) return false;

    if (kind === "chest") {
      // Path 3: None of the 3 cards is a selected chest item -> press "重抽全部" until a selected item appears
      if (perks.rerollAll !== false && !cards.some((c) => isPriorityPickCard(c, jobId, "chest"))) {
        if (clickPkAct(picker, isRerollDeckBtn)) {
          toast(L("rerollAll"));
          return true;
        }
      }
      // Path 2-2-2: If "重抽卡片" is available/enabled, reroll unmatched chest card until a selected item appears
      if (perks.rerollCard !== false) {
        const ordered = [
          ...cards.filter((c) => !isPriorityPickCard(c, jobId, "chest") && chestCardHasPlannedSlot(c, jobId)),
          ...cards.filter((c) => !isPriorityPickCard(c, jobId, "chest") && !chestCardHasPlannedSlot(c, jobId)),
        ];
        for (const card of ordered) {
          if (clickRerollCardOn(card)) {
            toast(L("rerollCard"));
            return true;
          }
        }
      }
      return false;
    }

    // Path 3 (Skills): None of the 3 cards is in 出戰技能 -> press "重抽全部"
    if (perks.rerollAll !== false && !cards.some((c) => isCombatSkillCard(c, jobId))) {
      if (clickPkAct(picker, isRerollDeckBtn)) {
        toast(L("rerollAll"));
        return true;
      }
    }
    return false;
  }

  function isFocusBtn(btn) {
    const act = btn.dataset.act || "";
    if (act.startsWith("bar:")) return false;
    return /專注|专注|聚焦|Focus|Focar|Enfocar/i.test(actText(btn));
  }

  function clickFocusOnCard(card) {
    const slot = card.closest(".pk-slot");
    if (!slot || slot.classList.contains("asking")) return null;
    return [...slot.querySelectorAll("button.pk-act")].find((b) => !b.disabled && isFocusBtn(b)) || null;
  }


  const BASIC_ATK_NAMES = ["普通攻擊", "Basic attack", "Ataque básico", "O ataque básico"];

  function cardIconId(card) {
    const img = card.querySelector(".pk-art img, img");
    const src = img?.getAttribute("src") || "";
    const m = src.match(/\/icons\/([^/?#]+)\.(?:png|webp)/i);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function sameAsset(a, b) {
    if (!a || !b) return false;
    const na = String(a).split("?")[0].split("#")[0];
    const nb = String(b).split("?")[0].split("#")[0];
    if (na === nb) return true;
    const ta = na.split("/").pop();
    const tb = nb.split("/").pop();
    return !!(ta && tb && ta === tb);
  }

  function basicAttackSkillName() {
    const g = combatGame;
    if (!g || !g.basicAttack || typeof g.skillDef !== "function") return "";
    try {
      const def = g.skillDef(g.basicAttack);
      return def && def.name ? String(def.name).trim() : "";
    } catch (_) {
      return "";
    }
  }

  function isBasicAttackCard(card) {
    const img = card.querySelector(".pk-art img, img");
    const src = img?.getAttribute("src") || img?.src || "";
    const icon = cardIconId(card);
    if (icon.startsWith("atk_")) return true;
    const id = skillIdFromCard(card);
    if (id && String(id).startsWith("atk_")) return true;
    const g = combatGame;
    const bid = g && (g.basicAttack || g.weaponBasic);
    if (bid && (id === bid || icon === bid)) return true;
    const name = (card.querySelector(".pk-name")?.textContent || "").trim();
    const sub = (card.querySelector("small.pk-sub")?.textContent || "").trim();
    const blob = `${name} ${sub}`.toLowerCase();
    if (BASIC_ATK_NAMES.some((s) => {
      const k = s.toLowerCase();
      const n = name.toLowerCase();
      return n === k || n.startsWith(k + " ") || n.startsWith(k + " ·") || blob.includes(k);
    })) return true;
    const defName = basicAttackSkillName();
    if (defName) {
      const n = name.toLowerCase();
      const d = defName.toLowerCase();
      if (n === d || n.startsWith(d + " ") || n.startsWith(d + " ·")) return true;
    }
    const expect = basicAttackIcon();
    if (src && expect && sameAsset(src, expect)) {
      if (g && g.stats && g.stats.infuse) return true;
      const w = g && g.loadout && g.loadout.weapon;
      const wid = w && (w.itemId != null ? w.itemId : w.id);
      if (wid != null && /\/items\//i.test(src)) return true;
    }
    return false;
  }

  function clickBanishOnCard(card) {
    const slot = card.closest(".pk-slot");
    if (!slot || slot.classList.contains("asking")) return null;
    return [...slot.querySelectorAll("button.pk-act")].find((b) => !b.disabled && isBanishBtn(b)) || null;
  }

  function perkCardId(card, kind) {
    if (kind === "chest") return itemIdFromCard(card);
    if (isBasicAttackCard(card)) return BASIC_SKILL_ID;
    return skillIdFromCard(card);
  }

  function tryExileBanish(picker, cards, jobId, kind) {
    const chest = kind === "chest";
    const perks = perkOf(jobId, chest ? "chest" : "skills");
    const fire = (card, sid) => {
      const btn = clickBanishOnCard(card);
      if (!btn) return false;
      lastPickAt = performance.now();
      btn.click();
      const name = (card.querySelector(".pk-name")?.textContent || "").trim();
      toast(`${L("exile")} · ${name || sid || L("basicAttack")}`);
      return true;
    };
    for (const card of cards) {
      const id = perkCardId(card, chest ? "chest" : "skills");
      if (!id) continue;
      const hit = id === BASIC_SKILL_ID ? perks.exileBasic : (perks.exile || []).includes(id);
      if (hit && fire(card, id)) return true;
    }
    return false;
  }

  function tryFocusPerk(picker, cards, jobId, kind) {
    const chest = kind === "chest";
    const perks = perkOf(jobId, chest ? "chest" : "skills");
    const fire = (card, sid) => {
      const btn = clickFocusOnCard(card);
      if (!btn) return false;
      lastPickAt = performance.now();
      btn.click();
      const name = (card.querySelector(".pk-name")?.textContent || "").trim();
      toast(`${L("focus")} · ${name || sid || L("basicAttack")}`);
      return true;
    };
    for (const card of cards) {
      const id = perkCardId(card, chest ? "chest" : "skills");
      if (!id) continue;
      const hit = id === BASIC_SKILL_ID ? perks.focusBasic : (perks.focus || []).includes(id);
      if (hit && fire(card, id)) return true;
    }
    return false;
  }



  function tryAutoDeitySwap() {
    if (featuresBlocked() || !store.auto) return;
    const dialogs = document.querySelectorAll(".ro-window, .overlay, .modal, [class*=confirm]");
    for (const d of dialogs) {
      if (d.classList && d.classList.contains("hidden")) continue;
      const txt = (d.textContent || "");
      if (!/交換|swap|cambiar|trocar|exchange/i.test(txt)) continue;
      if (!/神祇|Deity|Divindade/i.test(txt)) continue;
      const btns = [...d.querySelectorAll("button")];
      const yes = btns.find((b) => /是.*交換|Yes.*swap|Sí|Sim|交換|swap|confirm|確認/i.test(b.textContent || ""));
      if (yes && !yes.disabled) {
        lastPickAt = performance.now();
        yes.click();
        return true;
      }
    }
    return false;
  }
  function resolveCombatJob() {
    if (jobLocked && currentJob && JOBS[currentJob]) return currentJob;
    const det = detectJob();
    let job = (currentJob && JOBS[currentJob])
      ? currentJob
      : ((store.job && JOBS[store.job]) ? store.job : (det.raw && JOBS[det.raw] ? det.raw : (det.job || "swordsman")));
    if (det && det.raw && JOBS[det.raw]) {
      const hudParent = parentFirstJob(det.raw) || det.raw;
      const storeParent = parentFirstJob(job) || job;
      if (hudParent !== storeParent || (job === hudParent && det.raw !== hudParent && planOf(det.raw).skills.length)) {
        job = planOf(det.raw).skills.length ? det.raw : hudParent;
      }
    }
    return job;
  }

  function tryAutoPick(fromPoll) {
    if (featuresBlocked()) return;
    if (!store.auto) return;
    const picker = document.getElementById("picker");
    if (!picker || picker.classList.contains("hidden") || picker.classList.contains("closing")) {
      if (pickTimer) { clearTimeout(pickTimer); pickTimer = 0; }
      pickDueAt = 0;
      return;
    }
    if (!planUnlocked() && !combatGame) return;
    const title = (document.getElementById("pk-title")?.textContent || "").trim();
    const kind = pickerKind(title, picker);
    if (!kind) return;
    const cards = picker.querySelectorAll("#pk-cards .pk-card");
    if (!cards.length) return;
    const wait = 420 + cards.length * 120;
    const now = performance.now();
    // 避免 MutationObserver 頻繁觸發導致計時器被無限重置
    if (pickTimer && pickDueAt > now) return;
    if (!pickDueAt || pickDueAt <= now) pickDueAt = now + wait;
    const go = () => {
      pickTimer = 0;
      pickDueAt = 0;
      if (performance.now() - lastPickAt < 250) {
        tryAutoPick(true);
        return;
      }
      try { if (tryAutoDeitySwap()) return; } catch (_) {}
      const p = document.getElementById("picker");
      if (!p || p.classList.contains("hidden") || p.classList.contains("closing")) return;
      const t = (document.getElementById("pk-title")?.textContent || "").trim();
      const curKind = pickerKind(t, p);
      if (!curKind) return;
      const list = p.querySelectorAll("#pk-cards .pk-card");
      if (!list.length) return;
      const job = resolveCombatJob();

      const validCards = [...list].filter((c) => {
        const slot = c.closest(".pk-slot");
        return !(slot && slot.classList.contains("asking"));
      });
      if (!validCards.length) return;

      const { index, meta, disabledToReroll } = pickIndex(list, job, curKind);

      // 路徑1 & 路徑2：場上有符合「出戰技能」或寶箱已選「道具」
      if (index >= 0) {
        // 路徑2-1-2：技能強化項不在開啟排序中 -> 有「重抽卡片」就按重抽卡片，直到符合開啟排序或次數用完
        if (curKind === "levelup" && disabledToReroll && clickRerollCardOn(disabledToReroll)) {
          toast(L("rerollCard"));
          return;
        }
        const card = list[index];
        const slot = card.closest(".pk-slot");
        if (slot && slot.classList.contains("asking")) return;
        lastPickAt = performance.now();
        if (meta && meta.sid) {
          if (meta.pick) consumeAspect(skillAspectsOf(job, meta.sid), meta.sid, meta.pick, meta.exact);
          consumeLoadoutSkill(job, meta.sid);
        }
        card.click();
        const name = (card.querySelector(".pk-name")?.textContent || "").trim();
        toast(`${L("picked")} · ${name || "#" + (index + 1)}`);
        return;
      }

      // 路徑3 & 路徑2-2-2：沒有符合「出戰技能」或已選「道具」 -> 先重抽
      if (curKind === "levelup" || curKind === "chest") {
        if (tryPickerReroll(p, curKind, job)) return;

        // 最低優先度：技能列或道具列已滿時，檢查三張選項卡是否符合「放逐」或「專注」裡已選的技能或道具
        if (isBarFullForKind(p, curKind, job)) {
          if (tryExileBanish(p, validCards, job, curKind)) return;
          if (tryFocusPerk(p, validCards, job, curKind)) return;
        }

        const randCard = validCards[Math.floor(Math.random() * validCards.length)];
        const randIdx = [...list].indexOf(randCard);
        lastPickAt = performance.now();
        randCard.click();
        const name = (randCard.querySelector(".pk-name")?.textContent || "").trim();
        toast(`${L("picked")} · ${name || "#" + (randIdx + 1)}`);
      }
    };
    const delay = wait;
    pickDueAt = now + delay;
    pickTimer = setTimeout(go, delay);
  }

  /* -------------------- auto-move -------------------- */
  let combatGame = null;
  let lastSteer = { x: 0, y: 0, t: 0, kind: "" };
  let stickPickup = null;
  let lowHpDodge = false;
  let dodgeStick = { x: 0, y: 0, until: 0, mode: "" };
  let lastUserPointer = 0;
  let lastGameToken = 0;

  function isCombatGame(o) {
    return !!(o && typeof o === "object" && typeof o.moveTo === "function" && Array.isArray(o.pickups) && typeof o.chestCost === "function" && o.player);
  }

  // 讀取本地儲存或預設參數
  let cheatSettings = { godMode: false, hpThreshold: 50, damageMult: 1 };
  try {
    const saved = localStorage.getItem("ro-survivors-custom-cheats");
    if (saved) {
      const parsed = JSON.parse(saved);
      if (typeof parsed.godMode === "boolean") cheatSettings.godMode = parsed.godMode;
      if (typeof parsed.hpThreshold === "number") cheatSettings.hpThreshold = parsed.hpThreshold;
      if (typeof parsed.damageMult === "number") cheatSettings.damageMult = parsed.damageMult;
    }
  } catch (_) {}

  let experimentalGodMode = cheatSettings.godMode;
  let godModeHpThreshold = cheatSettings.hpThreshold || 50;
  let experimentalDamageMult = cheatSettings.damageMult;
  const DMG_MULTIPLIER_STEPS = [1, 2, 5, 10];

  function saveCheatSettings() {
    try {
      localStorage.setItem("ro-survivors-custom-cheats", JSON.stringify({
        godMode: experimentalGodMode,
        hpThreshold: godModeHpThreshold,
        damageMult: experimentalDamageMult
      }));
    } catch (_) {}
  }

  function togglePauseMode() {
    if (typeof window.__toggleBotPause === "function") {
      window.__toggleBotPause();
    } else {
      window.__BOT_PAUSED__ = !window.__BOT_PAUSED__;
      updateVisualStatusBadge();
    }
  }

  function updateVisualStatusBadge() {
    try {
      let panel = document.getElementById("ros-control-panel");
      if (!panel) {
        panel = document.createElement("div");
        panel.id = "ros-control-panel";
        panel.style.position = "fixed";
        panel.style.top = "14px";
        panel.style.left = "14px";
        panel.style.zIndex = "9999999";
        panel.style.display = "flex";
        panel.style.gap = "8px";
        panel.style.alignItems = "center";
        panel.style.userSelect = "none";

        // 按鈕 1: F2 暫停/恢復開關 (常駐統合於頂部面板第一位，永不遺失)
        const btnPause = document.createElement("button");
        btnPause.id = "ros-btn-pause";
        btnPause.title = "點擊或按 F2 暫停 / 恢復 BOT 自動掛機運作";
        btnPause.style.padding = "6px 14px";
        btnPause.style.borderRadius = "20px";
        btnPause.style.fontSize = "12px";
        btnPause.style.fontFamily = "Nunito, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        btnPause.style.fontWeight = "bold";
        btnPause.style.cursor = "pointer";
        btnPause.style.transition = "all 0.2s ease";
        btnPause.style.boxShadow = "0 2px 8px rgba(0,0,0,0.3)";
        btnPause.onclick = (e) => {
          e.stopPropagation();
          togglePauseMode();
        };
        panel.appendChild(btnPause);

        // 按鈕 2: 擬真保護開關 (F3)
        const btnGod = document.createElement("button");
        btnGod.id = "ros-btn-god";
        btnGod.title = "點擊或按 F3 快速切換無敵鎖血模式";
        btnGod.style.padding = "6px 14px";
        btnGod.style.borderRadius = "20px";
        btnGod.style.fontSize = "12px";
        btnGod.style.fontFamily = "Nunito, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        btnGod.style.fontWeight = "bold";
        btnGod.style.cursor = "pointer";
        btnGod.style.transition = "all 0.2s ease";
        btnGod.style.boxShadow = "0 2px 8px rgba(0,0,0,0.3)";
        btnGod.onclick = (e) => {
          e.stopPropagation();
          toggleGodMode();
        };
        panel.appendChild(btnGod);

        // 按鈕 3: 攻擊倍數開關 (F4)
        const btnDmg = document.createElement("button");
        btnDmg.id = "ros-btn-dmg";
        btnDmg.title = "點擊或按 F4 循環切換攻擊倍數 (1X -> 2X -> 5X -> 10X)";
        btnDmg.style.padding = "6px 14px";
        btnDmg.style.borderRadius = "20px";
        btnDmg.style.fontSize = "12px";
        btnDmg.style.fontFamily = "Nunito, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        btnDmg.style.fontWeight = "bold";
        btnDmg.style.cursor = "pointer";
        btnDmg.style.transition = "all 0.2s ease";
        btnDmg.style.boxShadow = "0 2px 8px rgba(0,0,0,0.3)";
        btnDmg.onclick = (e) => {
          e.stopPropagation();
          cycleDamageMult();
        };
        panel.appendChild(btnDmg);

        document.body.appendChild(panel);

        // 外部聯動回呼：供 Playwright 與原生熱鍵同步
        window.__ROS_UPDATE_PAUSE_UI__ = (isPaused) => {
          window.__BOT_PAUSED__ = isPaused;
          updateVisualStatusBadge();
        };

        // 監聽 F2 / F3 / F4 全域熱鍵
        window.addEventListener("keydown", (e) => {
          if (e.key === "F2") {
            e.preventDefault();
            togglePauseMode();
          } else if (e.key === "F3") {
            e.preventDefault();
            toggleGodMode();
          } else if (e.key === "F4") {
            e.preventDefault();
            cycleDamageMult();
          }
        });
      }

      // 隱藏舊版獨立 __ro_bot_badge__ 徽章，避免雙重疊加
      const oldBadge = document.getElementById("__ro_bot_badge__");
      if (oldBadge) oldBadge.style.display = "none";

      const btnPause = document.getElementById("ros-btn-pause");
      const btnGod = document.getElementById("ros-btn-god");
      const btnDmg = document.getElementById("ros-btn-dmg");

      if (btnPause) {
        const isPaused = !!window.__BOT_PAUSED__;
        if (isPaused) {
          btnPause.style.background = "linear-gradient(135deg, #d97706, #b45309)";
          btnPause.style.color = "#fffbeb";
          btnPause.style.border = "1px solid #f59e0b";
          btnPause.style.boxShadow = "0 0 10px rgba(245, 158, 11, 0.6)";
          btnPause.innerHTML = `⏸️ BOT: 【已暫停】 <span style='font-size:10px;opacity:0.8;'>(F2)</span>`;
          btnPause.title = "點擊或按 F2 恢復 BOT 掛機自動運作";
        } else {
          btnPause.style.background = "linear-gradient(135deg, #166534, #14532d)";
          btnPause.style.color = "#dcfce7";
          btnPause.style.border = "1px solid #4ade80";
          btnPause.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
          btnPause.innerHTML = `🟢 BOT: 【運行中】 <span style='font-size:10px;opacity:0.8;'>(F2)</span>`;
          btnPause.title = "點擊或按 F2 暫停 BOT 掛機自動運作";
        }
      }

      if (btnGod) {
        if (experimentalGodMode) {
          btnGod.style.background = "linear-gradient(135deg, #0284c7, #0369a1)";
          btnGod.style.color = "#ffffff";
          btnGod.style.border = "1px solid #38bdf8";
          btnGod.style.boxShadow = "0 0 10px rgba(14, 165, 233, 0.6)";
          btnGod.innerHTML = `🛡️ 擬真保護: 【<${godModeHpThreshold}%鎖血】 <span style='font-size:10px;opacity:0.8;'>(F3)</span>`;
          btnGod.title = `點擊或按 F3 關閉。目前狀態：血量高於 ${godModeHpThreshold}% 正常受傷扣血；低於 ${godModeHpThreshold}% 自動鎖血保命，保留飄紅字與受傷閃紅效果！`;
        } else {
          btnGod.style.background = "linear-gradient(135deg, #4b5563, #374151)";
          btnGod.style.color = "#e5e7eb";
          btnGod.style.border = "1px solid #6b7280";
          btnGod.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
          btnGod.innerHTML = "🛡️ 擬真保護: 【關閉 OFF】 <span style='font-size:10px;opacity:0.8;'>(F3)</span>";
          btnGod.title = `點擊或按 F3 開啟複合擬真保護模式 (低於 ${godModeHpThreshold}% 鎖血 + 正常受傷飄紅字)`;
        }
      }

      if (btnDmg) {
        if (experimentalDamageMult > 1) {
          btnDmg.style.background = "linear-gradient(135deg, #f57c00, #e65100)";
          btnDmg.style.color = "#ffffff";
          btnDmg.style.border = "1px solid #ffb74d";
          btnDmg.style.boxShadow = "0 0 10px rgba(255, 152, 0, 0.6)";
          btnDmg.innerHTML = `⚔️ 攻擊: 【${experimentalDamageMult}X】 <span style='font-size:10px;opacity:0.8;'>(F4)</span>`;
        } else {
          btnDmg.style.background = "linear-gradient(135deg, #455a64, #263238)";
          btnDmg.style.color = "#eceff1";
          btnDmg.style.border = "1px solid #90a4ae";
          btnDmg.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
          btnDmg.innerHTML = "⚔️ 攻擊: 【1X 正常】 <span style='font-size:10px;opacity:0.8;'>(F4)</span>";
        }
      }
    } catch (_) {}
  }

  function toggleGodMode() {
    experimentalGodMode = !experimentalGodMode;
    if (combatGame) combatGame.god = false; // 保持原生 god 為 false，讓受傷計算與飄紅字正常運算
    saveCheatSettings();
    updateVisualStatusBadge();
    console.log("[ROS] 🛡️ 複合擬真保護切換為:", experimentalGodMode ? `開啟 (ON, <${godModeHpThreshold}%鎖血)` : "關閉 (OFF, 正常模式)");
  }

  function cycleDamageMult() {
    let currentIdx = DMG_MULTIPLIER_STEPS.indexOf(experimentalDamageMult);
    if (currentIdx === -1) currentIdx = 0;
    const nextIdx = (currentIdx + 1) % DMG_MULTIPLIER_STEPS.length;
    experimentalDamageMult = DMG_MULTIPLIER_STEPS[nextIdx];
    saveCheatSettings();
    updateVisualStatusBadge();
    console.log("[ROS] ⚔️ 攻擊倍數切換為:", experimentalDamageMult + "X");
  }

  function hookAdvance(game) {
    const proto = Object.getPrototypeOf(game);
    if (!proto || proto.__rosHooked) return;
    proto.__rosHooked = true;

    // 0. 核心防禦：阻斷官方反外掛 springTrap 陷阱 (徹底杜絕 MVP BOSS 圍攻與 onBanhammer 處罰)
    if (typeof proto.springTrap === "function") {
      proto.springTrap = function () {
        console.warn("[ROS] 🛡️ 官方 springTrap 陷阱已成功攔截阻斷！已阻止 MVP BOSS 圍攻與檢測處罰。");
        return;
      };
    }

    // 1. 攔截受傷核心 hurtPlayer (複合擬真保護模式：血量>門檻正常扣血飄字，血量<=門檻鎖血防致死)
    if (typeof proto.hurtPlayer === "function") {
      const origHurtPlayer = proto.hurtPlayer;
      proto.hurtPlayer = function (e, t, s) {
        if (!experimentalGodMode) {
          return origHurtPlayer.call(this, e, t, s);
        }

        const maxHp = (this.stats && typeof this.stats.maxHp === "number") ? this.stats.maxHp : 100;
        const threshold = Math.round(maxHp * (godModeHpThreshold / 100));

        // 若當前血量高於門檻 (如 50%)，正常承受傷害扣血，但單次傷害不致使血量跌破門檻
        if (this.hp > threshold) {
          origHurtPlayer.call(this, e, t, s);
          if (this.hp < threshold) {
            this.hp = threshold;
          }
          if (this.player) this.player.dead = false;
          return;
        }

        // 血量已 <= 門檻 (如 50%)，觸發保命鎖血：絕不扣血、絕不致死
        this.hp = Math.max(this.hp, threshold, 1);
        if (this.player) {
          this.player.dead = false;
          this.player.hurtFlash = 150; // 觸發角色受傷閃紅特效
          if (typeof this.player.onPlayerHit === "function") {
            try { this.player.onPlayerHit(t); } catch (_) {}
          }
        }

        // 視覺浮動傷害飄紅字：依然跳出真實受傷數字
        try {
          const dmgAmount = Math.max(1, Math.round(typeof e === "number" ? e : 10));
          if (typeof this.addNumber === "function" && this.player) {
            this.addNumber(dmgAmount, this.player.x, this.player.y, 90, 16732240, 1.4);
          }
        } catch (_) {}
      };
    }

    // 2. 攔截怪物受傷核心 damageEnemy (RO Survivors 原生傷害輸出函式)
    if (typeof proto.damageEnemy === "function") {
      const origDamageEnemy = proto.damageEnemy;
      proto.damageEnemy = function (e, t, a) {
        if (experimentalDamageMult > 1 && typeof t === "number") {
          t = Math.round(t * experimentalDamageMult);
        }
        return origDamageEnemy.call(this, e, t, a);
      };
    }

    // 3. 攔截傷害倍率 damageMultiplier
    if (typeof proto.damageMultiplier === "function") {
      const origDmgMult = proto.damageMultiplier;
      proto.damageMultiplier = function () {
        const base = origDmgMult.call(this);
        if (experimentalDamageMult > 1) {
          return base * experimentalDamageMult;
        }
        return base;
      };
    }

    // 4. 攔截主迴圈 advance
    const adv = proto.advance;
    if (typeof adv === "function") {
      proto.advance = function (e) {
        try {
          if (this && this.state === "playing") {
            // 擬真保護模式下保持原生 god 為 false，讓受傷計算與飄紅字正常運算
            this.god = false;
            if (this.player && experimentalGodMode) {
              this.player.dead = false;
            }
            rosSteer(this);
          }
        } catch (_) {}
        return adv.call(this, e);
      };
    }
  }

  function tryCapture(obj) {
    if (!isCombatGame(obj)) return;
    if (isResetScreen() || isLobbyScreen()) return;
    if (obj.state && obj.state !== "playing" && obj.state !== "paused" && obj.state !== "levelup" && obj.state !== "chest") return;
    if (combatGame !== obj) {
      combatGame = obj;
      resetRotation();
      lastSteer = { x: 0, y: 0, t: 0, kind: "" };
      stickPickup = null;
      lowHpDodge = false;
      dodgeStick = { x: 0, y: 0, until: 0, mode: "" };
      lastGameToken++;
    }
    hookAdvance(obj);
  }

  function flushPending() {
    for (const o of [...pendingGames]) {
      try { tryCapture(o); } catch (_) {}
      if (combatGame === o || !o || typeof o.moveTo !== "function") pendingGames.delete(o);
    }
  }

  function startPump() {
    if (installGameHook.pumping) return;
    installGameHook.pumping = true;
    const pump = () => {
      flushPending();
      if (pendingGames.size) requestAnimationFrame(pump);
      else installGameHook.pumping = false;
    };
    requestAnimationFrame(pump);
  }

  function installGameHook() {
    captureGame = (o) => {
      if (!o || typeof o !== "object") return;
      try { tryCapture(o); } catch (_) {}
      try { hookPlazaTick(o); } catch (_) {}
      if (!isCombatGame(o)) {
        pendingGames.add(o);
        startPump();
      }
    };
    flushPending();
    startPump();
  }

  function userSteering(g) {
    const ks = g.keys;
    if (ks && typeof ks.has === "function") {
      const names = ["w", "a", "s", "d", "arrowup", "arrowdown", "arrowleft", "arrowright", "up", "down", "left", "right"];
      for (const k of names) if (ks.has(k) || ks.has(k.toUpperCase()) || ks.has("Key" + k.toUpperCase())) return true;
      for (const k of ks) {
        const s = String(k).toLowerCase();
        if (/^(key[wasd]|arrow(up|down|left|right))$/.test(s)) return true;
      }
    }
    const tm = g.touchMove;
    if (tm && typeof tm === "object" && (Math.abs(tm.x) > 0.05 || Math.abs(tm.y) > 0.05)) return true;
    if (g.movingByTouch || g.touchId) return true;
    return false;
  }

  function nearestWalkable(g, x, y) {
    try {
      if (g.walk && typeof g.walk.nearestWalkable === "function") {
        const n = g.walk.nearestWalkable(x, y);
        if (Array.isArray(n) && n.length >= 2) return [n[0], n[1]];
      }
    } catch (_) {}
    return [x, y];
  }

  function moveToward(g, x, y, kind) {
    [x, y] = nearestWalkable(g, x, y);
    const now = performance.now();
    if (lastSteer.kind === kind && now - lastSteer.t < 180 && Math.hypot(x - lastSteer.x, y - lastSteer.y) < 18) return;
    lastSteer = { x, y, t: now, kind };
    try { g.moveTo(x, y); } catch (_) {}
  }

  function pickupList(g, kinds) {
    const want = new Set(kinds);
    const out = [];
    const list = g.pickups || [];
    for (const p of list) {
      if (!p || p.dead) continue;
      if (want.has(p.kind)) out.push(p);
    }
    return out;
  }

  function nearestOf(px, py, list) {
    let best = null, bestD = Infinity;
    for (const p of list) {
      const d = (p.x - px) * (p.x - px) + (p.y - py) * (p.y - py);
      if (d < bestD) { bestD = d; best = p; }
    }
    return best;
  }

  const fxPrev = new WeakMap();
  let fxFrame = 0;

  function noteFx(f) {
    const ax = f.anchor.x, ay = f.anchor.y;
    let rec = fxPrev.get(f);
    if (!rec || rec.frame !== fxFrame) {
      rec = { x: ax, y: ay, px: rec ? rec.x : ax, py: rec ? rec.y : ay, frame: fxFrame };
      fxPrev.set(f, rec);
    }
    return rec;
  }

  function hpRatio(g) {
    const max = g.stats && g.stats.maxHp;
    const hp = g.hp;
    if (!(max > 0) || typeof hp !== "number") return 1;
    return hp / max;
  }

  function moveOptsOf() {
    if (!store.moveOpts || typeof store.moveOpts !== "object") {
      store.moveOpts = { dodgeMob: true, dodgeBoss: true, pickup: true };
    }
    return store.moveOpts;
  }

  function mobDodgeActive(g) {
    if (moveOptsOf().dodgeMob === false) {
      lowHpDodge = false;
      return false;
    }
    if (g) {
      const r = hpRatio(g);
      if (r < 0.3) lowHpDodge = true;
      else if (r >= 0.3) lowHpDodge = false;
    }
    return lowHpDodge;
  }

  function bossDodgeActive() {
    return moveOptsOf().dodgeBoss !== false;
  }

  function pickupMoveActive() {
    return moveOptsOf().pickup !== false;
  }

  function isBossEnemy(e) {
    const b = e && e.def && e.def.boss;
    return !!b;
  }

  function pointInAnyHazardZone(g, x, y) {
    const sprites = g.world3d && g.world3d.groundSprites;
    if (!Array.isArray(sprites)) return false;
    for (const z of sprites) {
      if (!z || z.disposed) continue;
      if (typeof z.progress !== "number" || z.progress < 0 || z.progress >= 1) continue;
      const info = zoneInfo(z);
      if (info && pointInZone(info, x, y, 12)) return true;
    }
    return false;
  }

  function scoreDodgeDest(g, p, x, y, dist, awayUx, awayUy, perpUx, perpUy) {
    const [wx, wy] = nearestWalkable(g, x, y);
    const moved = Math.hypot(wx - p.x, wy - p.y);
    let s = moved * 0.9;
    if (moved < dist * 0.4) s -= 180;
    if (pointInAnyHazardZone(g, wx, wy)) s -= 220;

    if (moved > 1) {
      const mvx = (wx - p.x) / moved;
      const mvy = (wy - p.y) / moved;
      if (awayUx || awayUy) {
        s += (mvx * awayUx + mvy * awayUy) * 42;
      }
      if (perpUx || perpUy) {
        s += Math.abs(mvx * perpUx + mvy * perpUy) * 55;
      }
    }

    const list = g.enemies || [];
    for (const e of list) {
      if (!e || e.dead || e.removed) continue;
      const boss = isBossEnemy(e);
      const safeR = boss ? 110 : 78;
      const d = Math.hypot(wx - e.x, wy - e.y);
      if (d < safeR) s -= (safeR - d) * (boss ? 2.4 : 1.65);
    }
    return { s, x: wx, y: wy };
  }

  function bestEscapeDest(g, p, fromX, fromY, dist, projVx, projVy) {
    const dx = p.x - fromX, dy = p.y - fromY;
    const len = Math.hypot(dx, dy) || 1;
    const awayUx = dx / len, awayUy = dy / len;
    let perpUx = 0, perpUy = 0;
    if (projVx || projVy) {
      const plen = Math.hypot(projVx, projVy) || 1;
      perpUx = -projVy / plen;
      perpUy = projVx / plen;
    }

    const dirs = [];
    // Include perpendicular & away vectors explicitly
    dirs.push([-awayUy, awayUx], [awayUy, -awayUx], [awayUx, awayUy]);
    if (perpUx || perpUy) {
      dirs.push([perpUx, perpUy], [-perpUx, -perpUy]);
    }
    // 12 radial directions (every 30 deg) to avoid getting cornered when surrounded
    for (let i = 0; i < 12; i++) {
      const ang = (i * Math.PI) / 6;
      dirs.push([Math.cos(ang), Math.sin(ang)]);
    }

    let best = null;
    for (const [ux, uy] of dirs) {
      const cand = scoreDodgeDest(g, p, p.x + ux * dist, p.y + uy * dist, dist, awayUx, awayUy, perpUx, perpUy);
      if (!best || cand.s > best.s) best = cand;
    }
    return best ? [best.x, best.y] : [p.x + awayUx * dist, p.y + awayUy * dist];
  }

  function sideStep(g, p, fromX, fromY, dist) {
    return bestEscapeDest(g, p, fromX, fromY, dist, 0, 0);
  }

  function commitDodge(g, x, y, mode, urgentBreak) {
    const now = performance.now();
    const hold = mode === "boss" ? 300 : 260;
    if (!urgentBreak && dodgeStick.mode === mode && now < dodgeStick.until) {
      const drift = Math.hypot(x - dodgeStick.x, y - dodgeStick.y);
      if (drift < 64) {
        x = dodgeStick.x;
        y = dodgeStick.y;
      }
    } else {
      [x, y] = nearestWalkable(g, x, y);
      dodgeStick = { x, y, until: now + hold, mode };
    }
    if (!urgentBreak && lastSteer.kind === "dodge-" + mode && now - lastSteer.t < 180 && Math.hypot(x - lastSteer.x, y - lastSteer.y) < 24) return;
    lastSteer = { x, y, t: now, kind: "dodge-" + mode };
    try { g.moveTo(x, y); } catch (_) {}
  }

  const PLAYER_R = 10;

  function zoneInfo(z) {
    const u = z && z.mat && z.mat.uniforms;
    if (!u || !u.shape) return null;
    return {
      shape: u.shape.value,
      half: u.halfAngle ? u.halfAngle.value : 0,
      x: z.x,
      y: z.y,
      w: z.w || 64,
      h: z.h || 64,
      rot: z.rotation || 0,
      progress: z.progress,
    };
  }

  function pointInZone(info, px, py, pad) {
    const dx = px - info.x, dy = py - info.y;
    const extra = PLAYER_R + pad;
    if (info.shape === 0) {
      const r = info.w / 2 + extra;
      return dx * dx + dy * dy < r * r;
    }
    if (info.shape === 3) {
      const r = info.w / 2;
      const r0 = (info.half || 0) * r;
      const d = Math.hypot(dx, dy);
      return d < r + extra && d > Math.max(0, r0 - extra);
    }
    if (info.shape === 1) {
      const r = info.w / 2 + extra;
      const dist = Math.hypot(dx, dy);
      if (dist > r) return false;
      if (dist < extra * 2) return true;
      let ang = Math.atan2(dy, dx) - info.rot;
      ang = Math.atan2(Math.sin(ang), Math.cos(ang));
      return Math.abs(ang) < info.half + extra / Math.max(dist, 1);
    }
    const ca = Math.cos(-info.rot), sa = Math.sin(-info.rot);
    const lx = dx * ca - dy * sa, ly = dx * sa + dy * ca;
    return Math.abs(lx) < info.w / 2 + extra && Math.abs(ly) < info.h / 2 + extra;
  }

  function escapeZone(g, p, info) {
    const pad = 28;
    const dx = p.x - info.x, dy = p.y - info.y;
    if (info.shape === 3) {
      const r = info.w / 2;
      const r0 = (info.half || 0) * r;
      const d = Math.hypot(dx, dy) || 0.001;
      const hole = Math.max(0, r0 - PLAYER_R - 8);
      if (d <= hole) return null;
      if (!pointInZone(info, p.x, p.y, 16)) return null;
      const toHole = d - hole * 0.55;
      const toOut = r + PLAYER_R + pad - d;
      if (hole >= 28 && toHole <= toOut + 10) {
        const target = hole * 0.45;
        return nearestWalkable(g, info.x + dx * (target / d), info.y + dy * (target / d));
      }
      const k = (r + PLAYER_R + pad) / d;
      return nearestWalkable(g, info.x + dx * k, info.y + dy * k);
    }
    if (!pointInZone(info, p.x, p.y, 16)) return null;
    if (info.shape === 0) {
      const r = info.w / 2 + PLAYER_R + pad;
      const d = Math.hypot(dx, dy) || 1;
      return nearestWalkable(g, info.x + dx / d * r, info.y + dy / d * r);
    }
    if (info.shape === 1) {
      const a = Math.atan2(dy, dx);
      let rel = a - info.rot;
      rel = Math.atan2(Math.sin(rel), Math.cos(rel));
      const sign = rel >= 0 ? 1 : -1;
      const outAng = info.rot + sign * (info.half + 0.45);
      const rr = info.w / 2 + PLAYER_R + pad;
      return nearestWalkable(g, info.x + Math.cos(outAng) * rr, info.y + Math.sin(outAng) * rr);
    }
    const ca = Math.cos(-info.rot), sa = Math.sin(-info.rot);
    const lx = dx * ca - dy * sa, ly = dx * sa + dy * ca;
    const sign = ly >= 0 ? 1 : -1;
    const out = info.h / 2 + PLAYER_R + pad;
    const c = Math.cos(info.rot), s = Math.sin(info.rot);
    return nearestWalkable(g, info.x + lx * c - sign * out * s, info.y + lx * s + sign * out * c);
  }

  function findBells(g) {
    const list = g.world3d && g.world3d.cylinders;
    const out = [];
    if (!Array.isArray(list)) return out;
    for (const o of list) {
      if (!o || o.disposed) continue;
      if (typeof o.out === "number" && o.out >= 0) continue;
      if (typeof o.waveAge === "number" && o.waveAge > 0.25) continue;
      const uni = o.groundMat && o.groundMat.uniforms && o.groundMat.uniforms.safeR;
      const safeR = uni ? uni.value : (o.safeR || (o.o && o.o.safeR));
      if (!(safeR > 0)) continue;
      if (typeof o.toll !== "function" && !uni && o.o?.kind !== "bell") continue;
      const mesh = o.mesh;
      const x = mesh && mesh.position ? mesh.position.x : (typeof o.x === "number" ? o.x : 0);
      const y = mesh && mesh.position ? mesh.position.z : (typeof o.y === "number" ? o.y : 0);
      out.push({ x, y, r: safeR, charge: o.charge || 0 });
    }
    return out;
  }

  function findFirePatches(g) {
    const list = g.world3d && g.world3d.cylinders;
    const out = [];
    if (!Array.isArray(list)) return out;
    for (const o of list) {
      if (!o || !(o.reach > 0) || !o.o || !(o.o.duration > 0)) continue;
      if (o.flameMat == null) continue;
      const life = 220 + o.o.duration;
      if ((o.age || 0) >= life) continue;
      const mesh = o.mesh;
      const x = mesh && mesh.position ? mesh.position.x : 0;
      const y = mesh && mesh.position ? mesh.position.z : 0;
      out.push({ x, y, r: o.reach, progress: Math.min(1, (o.age || 0) / life) });
    }
    return out;
  }

  function pickSafePointInBell(g, p, b, fires) {
    const maxSafe = Math.max(10, b.r - PLAYER_R - 8);
    const [cx, cy] = nearestWalkable(g, b.x, b.y);
    const inFire = (x, y) => fires.some((f) => Math.hypot(x - f.x, y - f.y) < f.r + PLAYER_R + 10);
    if (!inFire(cx, cy)) return [cx, cy];
    let bestPt = [cx, cy], bestScore = -1e9;
    for (let rad = 12; rad <= maxSafe; rad += 12) {
      for (let i = 0; i < 12; i++) {
        const ang = (i * Math.PI) / 6;
        const [wx, wy] = nearestWalkable(g, b.x + Math.cos(ang) * rad, b.y + Math.sin(ang) * rad);
        if (Math.hypot(wx - b.x, wy - b.y) > maxSafe) continue;
        let sc = -Math.hypot(wx - p.x, wy - p.y) * 0.25;
        for (const f of fires) {
          const fd = Math.hypot(wx - f.x, wy - f.y);
          if (fd < f.r + PLAYER_R + 12) sc -= (f.r + PLAYER_R + 12 - fd) * 20;
        }
        if (sc > bestScore) {
          bestScore = sc;
          bestPt = [wx, wy];
        }
      }
    }
    return bestPt;
  }

  function dodgeBossHazards(g, p) {
    let best = null, bestUrgency = 0;
    const fires = findFirePatches(g);

    const bells = findBells(g);
    if (bells.length) {
      let targetBell = null, bestBellScore = -1e9;
      for (const b of bells) {
        const d = Math.hypot(p.x - b.x, p.y - b.y);
        const inside = d <= Math.max(12, b.r - PLAYER_R - 6);
        const sc = (inside ? 500 : 0) + (b.charge || 0) * 120 - d;
        if (sc > bestBellScore) {
          bestBellScore = sc;
          targetBell = b;
        }
      }
      if (targetBell) {
        const d = Math.hypot(p.x - targetBell.x, p.y - targetBell.y);
        const safe = Math.max(10, targetBell.r - PLAYER_R - 8);
        const pt = pickSafePointInBell(g, p, targetBell, fires);
        if (d > safe) return pt;
        if (Math.hypot(p.x - pt[0], p.y - pt[1]) > 8) return pt;
        return [p.x, p.y];
      }
    }

    const sprites = g.world3d && g.world3d.groundSprites;
    if (Array.isArray(sprites)) {
      for (const z of sprites) {
        if (!z || z.disposed) continue;
        if (typeof z.progress !== "number" || z.progress < 0 || z.progress >= 1) continue;
        const info = zoneInfo(z);
        let dest = null;
        if (info) dest = escapeZone(g, p, info);
        else {
          const zx = z.x, zy = z.y;
          const ang = z.rotation || 0;
          const hw = (z.w || 64) / 2, hh = (z.h || 64) / 2;
          const ca = Math.cos(-ang), sa = Math.sin(-ang);
          const dx = p.x - zx, dy = p.y - zy;
          const lx = dx * ca - dy * sa, ly = dx * sa + dy * ca;
          if (Math.abs(lx) > hw + 28 || Math.abs(ly) > hh + 28) continue;
          dest = sideStep(g, p, zx, zy, 150);
        }
        if (!dest) continue;
        // Dig / circle telegraphs: react early, especially as progress ramps
        const shape = info && info.shape;
        const prog = z.progress || 0;
        let urg = 0.85 + prog;
        if (shape === 0) urg = 1.05 + prog * 0.5; // circular dig - highest priority
        if (shape === 3) urg = 0.95 + prog * 0.4;
        if (urg > bestUrgency) {
          bestUrgency = urg;
          best = dest;
        }
      }
    }

    for (const fire of findFirePatches(g)) {
      const d = Math.hypot(p.x - fire.x, p.y - fire.y);
      if (d >= fire.r + PLAYER_R + 16) continue;
      const urg = 0.88 + fire.progress * 0.2;
      if (urg > bestUrgency) {
        bestUrgency = urg;
        const len = d || 1;
        const rr = fire.r + PLAYER_R + 28;
        best = nearestWalkable(g, fire.x + (p.x - fire.x) / len * rr, fire.y + (p.y - fire.y) / len * rr);
      }
    }

    const fxs = g.fx;
    if (Array.isArray(fxs)) {
      for (const f of fxs) {
        if (!f || !f.upright || !f.anchor) continue;
        const rec = noteFx(f);
        const ax = rec.x, ay = rec.y, prev = { x: rec.px, y: rec.py };
        const fromBoss = (g.enemies || []).some((e) => {
          if (!isBossEnemy(e) || e.dead) return false;
          return Math.hypot(prev.x - e.x, prev.y - e.y) < 90;
        });
        if (!fromBoss) continue;
        let pt = null, urg = 0;
        if (prev.x !== ax || prev.y !== ay) {
          const vx = ax - prev.x, vy = ay - prev.y;
          const sp = Math.hypot(vx, vy);
          if (sp >= 0.4) {
            const rx = p.x - ax, ry = p.y - ay;
            const tHit = Math.max(0, (rx * vx + ry * vy) / (sp * sp));
            const miss = Math.hypot(p.x - (ax + vx * tHit), p.y - (ay + vy * tHit));
            const travel = tHit * sp;
            if (miss < 36 && travel < 200) {
              pt = sideStep(g, p, ax, ay, 140);
              urg = 0.8 + Math.max(0, 1 - travel / 200) * 0.2;
            }
          }
        }
        if (!urg) {
          const d = Math.hypot(p.x - ax, p.y - ay);
          if (d >= 12 && d <= 90) {
            pt = sideStep(g, p, ax, ay, 140);
            urg = 0.72;
          }
        }
        if (pt && urg > bestUrgency) {
          bestUrgency = urg;
          best = pt;
        }
      }
    }

    const now = g.time || 0;
    let fx = 0, fy = 0, threat = 0, cx = 0, cy = 0;
    for (const e of g.enemies || []) {
      if (!isBossEnemy(e) || e.dead || e.removed) continue;
      if ((e.hiddenUntil || 0) > now) continue;
      if (!(e.def && (e.def.damage > 0) || e.damage > 0)) continue;
      const rad = ((e.def && e.def.radius) || 20) + 16;
      const dx = p.x - e.x, dy = p.y - e.y;
      const d = Math.hypot(dx, dy) || 1;
      if (d >= rad + 40) continue;
      const w = (rad + 40 - d) / (rad + 40);
      fx += (dx / d) * w;
      fy += (dy / d) * w;
      cx += e.x * w;
      cy += e.y * w;
      threat += w;
    }
    if (threat > 0) {
      const urg = 0.7 + Math.min(0.3, threat * 0.25);
      if (urg > bestUrgency) {
        bestUrgency = urg;
        best = sideStep(g, p, cx / threat, cy / threat, 160);
      }
    }
    return best;
  }

  function dodgeMobHazards(g, p) {
    let best = null, bestUrgency = 0, urgent = false;
    const now = g.time || 0;

    // 1. Close-range normal monster projectiles (g.fx upright effects not spawned by bosses)
    const fxs = g.fx;
    if (Array.isArray(fxs)) {
      for (const f of fxs) {
        if (!f || !f.upright || !f.anchor) continue;
        const rec = noteFx(f);
        const ax = rec.x, ay = rec.y, prev = { x: rec.px, y: rec.py };
        const fromBoss = (g.enemies || []).some((e) => isBossEnemy(e) && !e.dead && Math.hypot(prev.x - e.x, prev.y - e.y) < 90);
        if (fromBoss) continue;
        const vx = ax - prev.x, vy = ay - prev.y;
        const sp = Math.hypot(vx, vy);
        if (sp >= 0.35) {
          const rx = p.x - ax, ry = p.y - ay;
          const tHit = Math.max(0, (rx * vx + ry * vy) / (sp * sp));
          const miss = Math.hypot(p.x - (ax + vx * tHit), p.y - (ay + vy * tHit));
          const travel = tHit * sp;
          if (miss < 28 && travel < 105) {
            const urg = 0.85 + Math.max(0, 1 - travel / 105) * 0.25;
            if (urg > bestUrgency) {
              bestUrgency = urg;
              best = bestEscapeDest(g, p, ax, ay, 135, vx, vy);
              if (travel < 55) urgent = true;
            }
          }
        } else {
          const d = Math.hypot(p.x - ax, p.y - ay);
          if (d >= 8 && d <= 48) {
            const urg = 0.72 + Math.max(0, (48 - d) / 48) * 0.18;
            if (urg > bestUrgency) {
              bestUrgency = urg;
              best = bestEscapeDest(g, p, ax, ay, 130, 0, 0);
            }
          }
        }
      }
    }

    // 2. Close-range normal monster explicit projectile arrays
    for (const arr of [g.projectiles, g.enemyProjectiles, g.bullets]) {
      if (!Array.isArray(arr)) continue;
      for (const pr of arr) {
        if (!pr || pr.dead || pr.removed || pr.friendly || pr.fromPlayer) continue;
        const px = pr.x, py = pr.y;
        if (!Number.isFinite(px) || !Number.isFinite(py)) continue;
        const vx = pr.vx || 0, vy = pr.vy || 0;
        const sp = Math.hypot(vx, vy);
        if (sp >= 0.35) {
          const rx = p.x - px, ry = p.y - py;
          const tHit = Math.max(0, (rx * vx + ry * vy) / (sp * sp));
          const miss = Math.hypot(p.x - (px + vx * tHit), p.y - (py + vy * tHit));
          const travel = tHit * sp;
          if (miss < 28 && travel < 105) {
            const urg = 0.86 + Math.max(0, 1 - travel / 105) * 0.24;
            if (urg > bestUrgency) {
              bestUrgency = urg;
              best = bestEscapeDest(g, p, px, py, 135, vx, vy);
              if (travel < 55) urgent = true;
            }
          }
        } else {
          const d = Math.hypot(p.x - px, p.y - py);
          if (d < 46) {
            const urg = 0.76;
            if (urg > bestUrgency) {
              bestUrgency = urg;
              best = bestEscapeDest(g, p, px, py, 130, 0, 0);
            }
          }
        }
      }
    }

    // 3. Immediate melee-range normal monster avoidance (only when monster is right next to player)
    let threat = 0, cx = 0, cy = 0, minGap = Infinity;
    for (const e of g.enemies || []) {
      if (!e || e.dead || e.removed || isBossEnemy(e)) continue;
      if ((e.hiddenUntil || 0) > now) continue;
      if (!((e.def && e.def.damage > 0) || e.damage > 0)) continue;
      const rad = ((e.def && e.def.radius) || 14) + PLAYER_R;
      const detectR = rad + 16;
      const d = Math.hypot(p.x - e.x, p.y - e.y);
      if (d >= detectR) continue;
      const gap = d - rad;
      if (gap < minGap) minGap = gap;
      const attacking = (e.windup > 0 || e.attacking || e.casting) ? 1.4 : 1;
      const w = Math.pow((detectR - d) / detectR, 1.2) * attacking;
      cx += e.x * w;
      cy += e.y * w;
      threat += w;
    }
    if (threat > 0) {
      const urg = 0.8 + Math.min(0.35, threat * 0.3);
      if (urg > bestUrgency) {
        bestUrgency = urg;
        best = bestEscapeDest(g, p, cx / threat, cy / threat, 140, 0, 0);
        if (minGap < 10) urgent = true;
      }
    }
    return best ? { dest: best, urgent } : null;
  }

  function alivePickup(g, p) {
    return !!(p && !p.dead && Array.isArray(g.pickups) && g.pickups.includes(p));
  }

  function pickSticky(g, list) {
    if (stickPickup && alivePickup(g, stickPickup) && list.includes(stickPickup)) return stickPickup;
    const pl = g.player;
    const next = nearestOf(pl.x, pl.y, list);
    stickPickup = next || null;
    return next;
  }

  function goPickup(g, p, kind) {
    if (!p) return false;
    stickPickup = p;
    moveToward(g, p.x, p.y, kind);
    return true;
  }

  function inLootPhase(g) {
    const game = g || combatGame;
    return !!(game && typeof game.lootUntil === "number" && game.lootUntil > 0);
  }

  function stageEnding(g) {
    const game = g || combatGame;
    try {
      if (game && (game.state === "playing" || game.state === "paused")) return false;
      if (document.body.classList.contains("gameover") || document.body.classList.contains("victory")) return true;
      const go = document.getElementById("gameover");
      if (go && !go.classList.contains("hidden")) return true;
      const results = document.getElementById("results") || document.getElementById("run-results") || document.querySelector(".results, .run-summary");
      if (results && !results.classList.contains("hidden")) return true;
      if (!game) return false;
      if (game.state && game.state !== "playing" && game.state !== "paused") return true;
      if (game.victory || game.won || game.cleared || game.ended || game.gameOver) return true;
      if (typeof game.lootUntil === "number" && game.lootUntil >= 0) return true;
      if (game.lootPhase || game.inLoot || game.postBoss || game.stageClear) return true;
      if (typeof game.timeLeft === "number" && game.timeLeft <= 0) return true;
      if (typeof game.remain === "number" && game.remain <= 0) return true;
      // Boss dead and no living enemies left often means stage wrap-up with leftover pickers
      const enemies = game.enemies;
      if (Array.isArray(enemies) && enemies.length) {
        const alive = enemies.some((e) => e && !e.dead && !e.removed);
        const hadBoss = enemies.some((e) => e && (e.boss || (e.def && e.def.boss) || (typeof isBossEnemy === "function" && isBossEnemy(e))));
        if (hadBoss && !alive && (game.waveDone || game.cleared || game.bossDead || game.finalBossDead)) return true;
      }
    } catch (_) {}
    return false;
  }

  function stopSteer(g) {
    stickPickup = null;
    lastSteer = { x: 0, y: 0, t: 0, kind: "" };
    dodgeStick = { x: 0, y: 0, until: 0, mode: "" };
    try { if (g) g.movePath = null; } catch (_) {}
  }

  function rosSteer(g) {
    if (featuresBlocked()) return;
    if (!planUnlocked()) return;
    if (!store.autoMove) return;
    if (!g || g.state !== "playing") return;
    const pl = g.player;
    if (!pl || pl.dead) return;
    const picker = document.getElementById("picker");
    if (picker && !picker.classList.contains("hidden")) return;
    if (userSteering(g)) return;

    fxFrame++;
    const hasActiveBell = bossDodgeActive() && findBells(g).length > 0;
    if (hasActiveBell) {
      const bossDodge = dodgeBossHazards(g, pl);
      if (bossDodge) {
        commitDodge(g, bossDodge[0], bossDodge[1], "boss", true);
        return;
      }
    }
    if (mobDodgeActive(g)) {
      const mobDodge = dodgeMobHazards(g, pl);
      if (mobDodge) {
        commitDodge(g, mobDodge.dest[0], mobDodge.dest[1], "mob", true);
        return;
      }
    }
    if (bossDodgeActive()) {
      const bossDodge = dodgeBossHazards(g, pl);
      if (bossDodge) {
        commitDodge(g, bossDodge[0], bossDodge[1], "boss", false);
        return;
      }
    }
    if (performance.now() - lastUserPointer < 1200) return;

    if (inLootPhase(g)) {
      stopSteer(g);
      return;
    }

    if (!pickupMoveActive()) {
      stickPickup = null;
      return;
    }

    // Priority order (left to right): 經驗 (EXP) -> 金幣 (Zeny) -> 磁力 (Magnet) -> 箱子 (Chest, only if enough Zeny)
    const gem = pickSticky(g, pickupList(g, ["gem_blue", "gem_yellow", "gem_red"]));
    if (gem) { goPickup(g, gem, "gem"); return; }

    const zeny = pickSticky(g, pickupList(g, ["zeny"]));
    if (zeny) { goPickup(g, zeny, "zeny"); return; }

    const magnet = pickSticky(g, pickupList(g, ["magnet"]));
    if (magnet) { goPickup(g, magnet, "magnet"); return; }

    let canChest = false;
    try { canChest = typeof g.zeny === "number" && typeof g.chestCost === "function" && g.zeny >= g.chestCost(); } catch (_) {}
    if (canChest) {
      const chests = pickupList(g, ["chest"]);
      if (chests.length) {
        const chest = pickSticky(g, chests);
        if (chest) {
          const d2 = (chest.x - pl.x) * (chest.x - pl.x) + (chest.y - pl.y) * (chest.y - pl.y);
          if (d2 < 1156 && typeof g.tryOpenChest === "function") {
            try { g.tryOpenChest(chest); } catch (_) {}
            if (g.state !== "playing" || g.openingChest) return;
          }
          goPickup(g, chest, "chest");
          return;
        }
      }
    }

    stickPickup = null;
  }



  function farmPetsList() {
    return (DATA.farm.pets || []).filter((p) => p && p.obtain !== "evolution");
  }
  function defaultFarm() {
    return { enabled: false, stage: "auto", missingOnly: true, equip: [], cards: [], pets: [] };
  }
  function migrateFarm(raw) {
    const f = defaultFarm();
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return f;
    f.enabled = !!raw.enabled;
    if (typeof raw.stage === "string") f.stage = raw.stage;
    f.missingOnly = raw.missingOnly !== false;
    if (Array.isArray(raw.equip)) {
      f.equip = raw.equip.map((e) => {
        const id = Number(e && e.id);
        if (!Number.isFinite(id)) return null;
        const minQuality = Math.max(0, Math.min(4, Number(e.minQuality) || 0));
        const affixes = Array.isArray(e.affixes) ? e.affixes.filter((a) => typeof a === "string") : [];
        return { id, minQuality, affixes };
      }).filter(Boolean);
    }
    if (Array.isArray(raw.cards)) f.cards = raw.cards.map(Number).filter((n) => Number.isFinite(n));
    if (Array.isArray(raw.pets)) f.pets = raw.pets.filter((id) => typeof id === "string");
    if (f.equip.length) { f.cards = []; f.pets = []; f.equip = f.equip.slice(0, 1); }
    else if (f.cards.length) { f.pets = []; f.cards = f.cards.slice(0, 1); }
    else f.pets = f.pets.slice(0, 1);
    return f;
  }
  function farmLang(names, fallback) {
    if (!names) return fallback || "";
    return names[lang] || names["zh-TW"] || names.en || names.es || names["pt-BR"] || fallback || "";
  }
  function farmHasTargets() {
    const f = store.farm;
    return !!(f && (f.equip.length || f.cards.length || f.pets.length));
  }
  function farmTargetsSig() {
    const f = store.farm || defaultFarm();
    return JSON.stringify({ e: f.equip, c: f.cards, p: f.pets });
  }
  const farmGot = new Set();
  let farmSig = "";
  let farmDoneToast = false;
  let farmLockToast = "";
  let farmActAt = 0;
  let farmRevealAt = 0;
  let farmPointer = false;
  let farmFilter = "all";
  let farmCardFilter = "all";
  let farmSel = null;
  let farmDraft = null;
  function resetFarmProgress() {
    farmGot.clear();
    farmDoneToast = false;
    farmLockToast = "";
    farmSig = farmTargetsSig();
  }
  function syncFarmSig() {
    const s = farmTargetsSig();
    if (s !== farmSig) resetFarmProgress();
  }
  function farmMissing() {
    const f = store.farm;
    return {
      equip: (f.equip || []).filter((e) => !farmGot.has("e:" + e.id)),
      cards: (f.cards || []).filter((id) => !farmGot.has("c:" + id)),
      pets: (f.pets || []).filter((id) => !farmGot.has("p:" + id)),
    };
  }
  function farmAllDone() {
    if (!farmHasTargets()) return false;
    const m = farmMissing();
    return !m.equip.length && !m.cards.length && !m.pets.length;
  }
  function farmableStages() {
    return (DATA.farm.stages || []).filter((s) => s.farmable);
  }
  function stagesOf(kind, id) {
    const list = kind === "equip" ? DATA.farm.equip : kind === "cards" ? DATA.farm.cards : DATA.farm.pets;
    const row = list.find((x) => String(x.id) === String(id));
    const ok = new Set(farmableStages().map((s) => s.id));
    return ((row && row.stages) || []).filter((sid) => ok.has(sid));
  }
  function pickFarmStage() {
    const forced = store.farm.stage;
    if (forced && forced !== "auto") return forced;
    const miss = farmMissing();
    const order = [
      ...miss.equip.map((e) => stagesOf("equip", e.id)),
      ...miss.cards.map((id) => stagesOf("cards", id)),
      ...miss.pets.map((id) => stagesOf("pets", id)),
    ];
    for (const stgs of order) if (stgs.length) return stgs[0];
    return null;
  }
  function farmListStage() {
    const s = store.farm.stage;
    if (s && s !== "auto") return s;
    return pickFarmStage() || ((farmableStages()[0] || {}).id) || null;
  }
  function dropsInFarmStage(it) {
    const sid = farmListStage();
    return !!(sid && it && (it.stages || []).includes(sid));
  }
  let farmOwnedCache = null;
  function farmOwned() {
    if (farmOwnedCache) return farmOwnedCache;
    const equip = new Set();
    const cards = new Set();
    const pets = new Set();
    const takeCards = (map) => {
      if (!map || typeof map !== "object" || Array.isArray(map)) return;
      for (const [id, n] of Object.entries(map)) {
        if (Number(n) > 0) cards.add(String(id));
      }
    };
    const takeInv = (list, ownerId) => {
      for (const it of list || []) {
        if (!it) continue;
        if (ownerId != null && it.owner && it.owner !== ownerId) continue;
        if (it.itemId != null) equip.add(Number(it.itemId));
        for (const c of it.cards || []) if (c != null && c !== "") cards.add(String(c));
      }
    };
    const acc = gameStoreGet("ro-survivors.account.v1") || {};
    const ch = charForPlan();
    const ownerId = ch && ch.id != null ? ch.id : null;
    takeInv(acc.inventory, ownerId);
    takeCards(acc.cards);
    if (ch) {
      if (Array.isArray(ch.inventory) && ch.inventory !== acc.inventory) takeInv(ch.inventory, ownerId);
      takeCards(ch.cards);
    }
    const raw = gameStoreGet("ro-survivors.pets.v1");
    const bag = raw && raw.pets;
    if (bag && typeof bag === "object") {
      for (const [id, rec] of Object.entries(bag)) {
        if (rec) pets.add(String(id));
      }
    }
    farmOwnedCache = { equip, cards, pets };
    return farmOwnedCache;
  }
  function charOwnsFarmItem(kind, id) {
    const o = farmOwned();
    if (kind === "equip") return o.equip.has(Number(id));
    if (kind === "cards") return o.cards.has(String(id));
    return o.pets.has(String(id));
  }
  function charHasAllFarmItems() {
    return !farmKindHasMissing("equip") && !farmKindHasMissing("cards") && !farmKindHasMissing("pets");
  }
  window.addEventListener("ro-account", () => { farmOwnedCache = null; });
  window.addEventListener("ro-save-replaced", () => { farmOwnedCache = null; });
  function farmIsAutoStage() {
    return !store.farm.stage || store.farm.stage === "auto";
  }
  function farmTabKind() {
    return (uiSub && uiSub.farm) || "equip";
  }
  function farmKindHasMissing(kind) {
    const k = kind || farmTabKind();
    const list = k === "equip" ? DATA.farm.equip : k === "cards" ? DATA.farm.cards : DATA.farm.pets;
    return (list || []).some((it) => !charOwnsFarmItem(k, it.id));
  }
  function farmMissingOnly() {
    return !store.farm || store.farm.missingOnly !== false;
  }
  function farmItemVisible(kind, it) {
    if (!it) return false;
    const inStage = farmIsAutoStage() || dropsInFarmStage(it);
    if (isFarmTarget(kind, it.id)) return inStage;
    if (!inStage) return false;
    if (farmMissingOnly()) return !charOwnsFarmItem(kind, it.id);
    return true;
  }
  function renderFarmStageNote() {
    if (farmIsAutoStage()) return null;
    const sid = farmListStage();
    const st = (DATA.farm.stages || []).find((x) => x.id === sid);
    const name = st ? farmLang(st.names, sid) : "";
    if (!name) return el("div", { class: "ros-muted ros-farm-stage-note" }, L("farmStageEmpty"));
    return el("div", { class: "ros-muted ros-farm-stage-note" }, `${L("farmShowing")}（${name}）`);
  }
  function farmCatalog(kind, id) {
    const list = kind === "equip" ? DATA.farm.equip : kind === "cards" ? DATA.farm.cards : DATA.farm.pets;
    return list.find((x) => String(x.id) === String(id));
  }
  function farmItemName(kind, id) {
    const row = farmCatalog(kind, id);
    return (row && row.name) || String(id);
  }
  function markFarmGot(key, label) {
    if (farmGot.has(key)) return;
    farmGot.add(key);
    toast(`${L("farmGot")}: ${label}`);
    if (farmAllDone() && !farmDoneToast) {
      farmDoneToast = true;
      setTimeout(() => toast(L("farmAllGot")), 1700);
    }
  }
  const UNID_RE = /未鑑定|sin identificar|unidentified|não identificad/i;
  function affixIdsOf(loot) {
    const list = (loot && (loot.affixes || loot.affix)) || [];
    const ids = [];
    for (const a of list) {
      if (a == null) continue;
      if (typeof a === "string") ids.push(a);
      else if (a.stat) ids.push(a.stat);
      else if (a.id) ids.push(a.id);
    }
    return ids;
  }
  function itemIsUnidentified(item) {
    return !!(item && item.unid);
  }
  function equipWantedMatch(item, forRoll) {
    if (!item) return null;
    const id = Number(item.id != null ? item.id : item.itemId);
    for (const w of store.farm.equip || []) {
      if (Number(w.id) !== id) continue;
      const q = Number(item.quality);
      if (Number.isFinite(q) && q < (w.minQuality || 0)) continue;
      if (!Number.isFinite(q) && (w.minQuality || 0) > 0) continue;
      const need = w.affixes || [];
      if (!need.length) return w;
      if (itemIsUnidentified(item)) return forRoll ? w : null;
      const have = affixIdsOf(item);
      if (need.every((a) => have.includes(a))) return w;
    }
    return null;
  }
  function parseDropReveal() {
    const box = document.getElementById("drop-reveal");
    if (!box || box.classList.contains("hidden")) return null;
    const img = box.querySelector("img");
    const src = (img && (img.getAttribute("src") || img.src)) || "";
    const mItem = src.match(/\/items\/(\d+)/);
    const mCard = src.match(/\/cards\/(\d+)/);
    const qName = ((box.querySelector(".dr-q") || {}).textContent || "").trim();
    const q = (DATA.farm.qualities || []).find((row) => Object.values(row.names || {}).includes(qName));
    const quality = q ? q.id : NaN;
    const blob = `${(box.querySelector(".dr-stats") || {}).textContent || ""} ${(box.querySelector(".dr-name") || {}).textContent || ""} ${qName}`;
    const low = blob.toLowerCase();
    const unid = UNID_RE.test(blob);
    const affixes = unid ? [] : (DATA.farm.affixes || []).filter((a) =>
      Object.values(a.names || {}).some((n) => n && low.includes(String(n).toLowerCase()))
    ).map((a) => a.id);
    if (mItem) {
      const id = Number(mItem[1]);
      const pet = DATA.farm.pets.find((p) => Number(p.egg) === id || p.id === String(id));
      if (pet) return { kind: "egg", id, pet };
      return { kind: "equip", id, quality, affixes, unid };
    }
    if (mCard) return { kind: "card", id: Number(mCard[1]) };
    return { kind: "unknown" };
  }
  function scanFarmInventories() {
    const bags = [];
    const seen = new Set();
    const add = (list) => {
      for (const it of list || []) {
        if (!it) continue;
        const key = it.uid || it.id || it.itemId;
        const sig = `${key}:${it.quality}:${affixIdsOf(it).join(",")}`;
        if (seen.has(sig)) continue;
        seen.add(sig);
        bags.push(it);
      }
    };
    add(accountInventory());
    for (const ch of chars()) add(charInventory(ch));
    for (const it of bags) {
      const w = equipWantedMatch(it);
      if (w) markFarmGot("e:" + w.id, farmItemName("equip", w.id));
    }
  }
  function scanFarmDrops() {
    scanFarmInventories();
    const g = combatGame;
    if (g) {
      for (const it of g.runLoot || []) {
        const w = equipWantedMatch(it);
        if (w) markFarmGot("e:" + w.id, farmItemName("equip", w.id));
      }
      for (const c of g.runCards || []) {
        const id = Number(c && c.id != null ? c.id : c);
        if ((store.farm.cards || []).some((x) => Number(x) === id)) markFarmGot("c:" + id, farmItemName("cards", id));
      }
      for (const egg of g.runEggs || []) {
        const pet = DATA.farm.pets.find((p) => Number(p.egg) === Number(egg) || p.id === egg);
        if (pet && (store.farm.pets || []).includes(pet.id)) markFarmGot("p:" + pet.id, pet.name);
      }
    }
    const parsed = parseDropReveal();
    if (!parsed) return;
    if (parsed.kind === "equip") {
      const w = equipWantedMatch(parsed);
      if (w) markFarmGot("e:" + w.id, farmItemName("equip", w.id));
    } else if (parsed.kind === "card") {
      if ((store.farm.cards || []).some((x) => Number(x) === Number(parsed.id))) {
        markFarmGot("c:" + parsed.id, farmItemName("cards", parsed.id));
      }
    } else if (parsed.kind === "egg" && parsed.pet && (store.farm.pets || []).includes(parsed.pet.id)) {
      markFarmGot("p:" + parsed.pet.id, parsed.pet.name);
    }
  }
  function farmOverlayOpen(id) {
    const n = document.getElementById(id);
    return !!(n && !n.classList.contains("hidden"));
  }
  function farmClickId(id) {
    const n = document.getElementById(id);
    if (!n || n.disabled || n.classList.contains("hidden")) return false;
    n.click();
    return true;
  }
  const FARM_KEEP_OVERLAY = new Set([
    "stages", "npc-dialog", "loading", "drop-reveal", "picker", "gameover",
    "charselect", "charcreate", "splash", "pause", "ros-farm-next", "ros-plan-gate",
  ]);
  const FARM_CLOSE = [
    ["cp-sock", "cp-sock-done"],
    ["shop", "shop-close"],
    ["wiki", "wk-close"],
    ["options", "opt-close"],
    ["petkeeper", "pk-close"],
    ["chronicle", "chr-close"],
    ["towerkeeper", "tk-close"],
    ["mailbox", "mb-close"],
    ["stylist", "st-close"],
    ["smith", "smith-close"],
    ["friends", "fr-close"],
    ["inspect", "ins-close"],
    ["trade", "tr-cancel"],
    ["news-popup", "news-close"],
    ["legal-popup", "legal-close"],
    ["portrait-picker", "pb-close"],
    ["charpanel", "cp-back"],
  ];
  function farmHideOurUi() {
    let hid = false;
    for (const id of ["ros-plan-ov", "ros-asp", "ros-plan-tip"]) {
      const n = document.getElementById(id);
      if (n && !n.classList.contains("hidden")) { n.classList.add("hidden"); hid = true; }
    }
    return hid;
  }
  let farmSawLobby = false;
  let farmNextUntil = 0;
  let farmNextDone = false;
  let farmNextTimer = 0;
  function farmNoteLobby(inLobby) {
    if (inLobby === farmSawLobby) return;
    farmSawLobby = inLobby;
    farmNextDone = false;
    farmNextUntil = 0;
    if (!inLobby) {
      hideFarmNext();
      farmStopKeyWalk();
    }
  }
  function hideFarmNext() {
    const el = document.getElementById("ros-farm-next");
    if (el) {
      el.classList.add("hidden");
      el.classList.remove("overlay");
    }
    if (farmNextTimer) { clearInterval(farmNextTimer); farmNextTimer = 0; }
  }
  function farmNextLeft() {
    return Math.max(1, Math.ceil((farmNextUntil - performance.now()) / 1000));
  }
  function syncFarmNextText() {
    const root = document.getElementById("ros-farm-next");
    if (!root) return;
    const title = root.querySelector(".ro-title");
    const text = document.getElementById("ros-farm-next-text");
    const btn = document.getElementById("ros-farm-next-cancel");
    if (title) title.textContent = L("farm");
    if (text) {
      const n = farmNextLeft();
      text.textContent = "";
      const parts = L("farmNext").split("{n}");
      text.appendChild(document.createTextNode(parts[0] || ""));
      const b = document.createElement("b");
      b.textContent = String(n);
      text.appendChild(b);
      text.appendChild(document.createTextNode(parts[1] || ""));
    }
    if (btn) btn.textContent = L("cancel");
  }
  function ensureFarmNextUi() {
    let el = document.getElementById("ros-farm-next");
    if (el) return el;
    el = document.createElement("div");
    el.id = "ros-farm-next";
    el.className = "overlay hidden";
    el.innerHTML = '<div class="ro-window small-window"><div class="ro-title"></div><div class="ro-body center"><div class="npc-text" id="ros-farm-next-text"></div></div><div class="btn-row pad"><button type="button" class="ro-btn" id="ros-farm-next-cancel"></button></div></div>';
    document.body.appendChild(el);
    el.querySelector("#ros-farm-next-cancel").addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      cancelFarmCountdown();
    });
    return el;
  }
  function cancelFarmCountdown() {
    hideFarmNext();
    farmNextDone = false;
    farmNextUntil = 0;
    farmStopKeyWalk();
    if (!store.farm) store.farm = defaultFarm();
    store.farm.enabled = false;
    saveStore();
    const inp = document.querySelector("#ros-plan-ov .ros-farm-opt input[type=checkbox]");
    if (inp) inp.checked = false;
    try { refreshBtn(); } catch (_) {}
  }
  function closeStageOverlayDuringCountdown() {
    if (farmOverlayOpen("stages")) {
      if (!farmClickId("stg-close")) {
        const stg = document.getElementById("stages");
        if (stg) stg.classList.add("hidden");
      }
    }
  }
  function finishFarmCountdown() {
    hideFarmNext();
    farmNextDone = true;
    farmNextUntil = 0;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (!store.farm || !store.farm.enabled || !farmNextDone) return;
      const nextEl = document.getElementById("ros-farm-next");
      if (nextEl && !nextEl.classList.contains("hidden")) return;
      try { farmTryCaptain(); } catch (_) {}
    }));
  }
  function startFarmCountdown() {
    if (farmNextDone) return;
    lang = gameLang();
    const now = performance.now();
    if (farmNextUntil && now >= farmNextUntil) {
      finishFarmCountdown();
      return;
    }
    if (!(farmNextUntil && now < farmNextUntil)) {
      farmNextUntil = now + 5000;
    }
    farmStopKeyWalk();
    closeStageOverlayDuringCountdown();
    const el = ensureFarmNextUi();
    el.classList.add("overlay");
    el.classList.remove("hidden");
    farmHideOurUi();
    syncFarmNextText();
    if (farmNextTimer) clearInterval(farmNextTimer);
    farmNextTimer = setInterval(() => {
      if (!store.farm || !store.farm.enabled) {
        hideFarmNext();
        farmNextDone = false;
        farmNextUntil = 0;
        return;
      }
      closeStageOverlayDuringCountdown();
      if (performance.now() >= farmNextUntil) {
        finishFarmCountdown();
        return;
      }
      syncFarmNextText();
    }, 100);
  }
  function farmAwaitNextRun() {
    if (farmNextDone) return false;
    if (farmNextUntil && performance.now() >= farmNextUntil) {
      finishFarmCountdown();
      return true;
    }
    const nextEl = document.getElementById("ros-farm-next");
    if (farmNextUntil && performance.now() < farmNextUntil && nextEl && !nextEl.classList.contains("hidden")) {
      closeStageOverlayDuringCountdown();
      return true;
    }
    startFarmCountdown();
    return true;
  }
  function farmCloseWindows() {
    if (farmClosePlayerMenu()) return true;
    for (const [id, btn] of FARM_CLOSE) {
      if (farmOverlayOpen(id) && farmClickId(btn)) return true;
    }
    for (const n of document.querySelectorAll(".overlay:not(.hidden)")) {
      if (!n.id || FARM_KEEP_OVERLAY.has(n.id) || n.id.startsWith("ros-")) continue;
      const btn = n.querySelector("button[id$='-close'], button[id$='-cancel'], button[id$='-done']");
      if (btn && !btn.disabled && btn.id !== "stg-close" && btn.id !== "cc-cancel") {
        btn.click();
        return true;
      }
    }
    return false;
  }
  function farmDismissDialog() {
    const dlg = document.getElementById("npc-dialog");
    if (!dlg || dlg.classList.contains("hidden")) return false;
    if (farmClickLabeled(dlg, FARM_LOBBY_OFFLINE)) return true;
    const opt = [...dlg.querySelectorAll("#npc-options button")].find((b) => !b.disabled);
    if (opt) { opt.click(); return true; }
    return false;
  }
  function farmPointerOn(el, x, y) {
    if (!el) return false;
    farmPointer = true;
    try {
      const opts = {
        bubbles: true, cancelable: true, clientX: x, clientY: y, view: window,
        pointerId: 1, pointerType: "touch", button: 0, buttons: 1, isPrimary: true,
      };
      el.dispatchEvent(new PointerEvent("pointerdown", opts));
      const up = Object.assign({}, opts, { buttons: 0 });
      el.dispatchEvent(new PointerEvent("pointerup", up));
      window.dispatchEvent(new PointerEvent("pointerup", up));
    } catch (_) {
      farmPointer = false;
      return false;
    }
    farmPointer = false;
    return true;
  }
  let lobbyGame = null;
  function isLobbyPlaza(o) {
    return !!(o && typeof o.moveTo === "function" && Array.isArray(o.npcs) && o.player
      && typeof o.chestCost !== "function" && !Array.isArray(o.pickups));
  }
  function hookPlazaTick(o) {
    if (!o || typeof o.tick !== "function") return;
    const proto = Object.getPrototypeOf(o);
    if (!proto || proto.__rosPlazaTick) return;
    const orig = proto.tick;
    if (typeof orig !== "function") return;
    proto.__rosPlazaTick = true;
    proto.tick = function (dt) {
      try {
        if (this && this.keys && Array.isArray(this.npcs) && this.player
            && typeof this.moveTo === "function" && typeof this.menuOpen === "function"
            && typeof this.chestCost !== "function" && !Array.isArray(this.pickups)) {
          livePlaza = this;
        }
      } catch (_) {}
      return orig.apply(this, arguments);
    };
  }
  function lobbyIsLive(o) {
    if (!isLobbyPlaza(o)) return false;
    try {
      if (o.prompt && o.prompt.isConnected) return true;
      if (o.nameLabel && o.nameLabel.isConnected) return true;
      if (o.entityLayer && o.entityLayer.parent) return true;
    } catch (_) {}
    return false;
  }
  function lobbyLiveScore(o) {
    if (!isLobbyPlaza(o)) return -1;
    let s = 0;
    const prompt = document.getElementById("lobby-prompt");
    const self = document.querySelector("#lobby-labels .lobby-name.self");
    const ui = document.getElementById("lobby-ui");
    if (o.prompt && prompt && o.prompt === prompt) s += 80;
    if (o.ui && ui && o.ui === ui) s += 20;
    if (self && o.nameLabel === self) s += 80;
    if (o.nameLabel && o.nameLabel.isConnected) s += 30;
    if (o.entityLayer && o.entityLayer.parent) s += 20;
    if (o.npcs && o.npcs.some((n) => n && n.id === "captain")) s += 10;
    return s;
  }
  function lobbyPlaza() {
    if (lobbyIsLive(livePlaza)) {
      hookPlazaTick(livePlaza);
      lobbyGame = livePlaza;
      return livePlaza;
    }
    let best = null, bestS = -1;
    const consider = (o) => {
      const s = lobbyLiveScore(o);
      if (s > bestS) { bestS = s; best = o; }
    };
    consider(lobbyGame);
    consider(livePlaza);
    for (const o of pendingGames) consider(o);
    if (bestS >= 0) {
      lobbyGame = best;
      hookPlazaTick(best);
    }
    return bestS >= 0 ? best : null;
  }
  function farmPlazaReady() {
    if (!document.body.classList.contains("in-lobby")) return false;
    const ui = document.getElementById("lobby-ui");
    if (ui && ui.classList.contains("hidden")) return false;
    return !!document.querySelector("#lobby-labels .lobby-name.npc");
  }
  function farmLoadingEntersStage() {
    const el = document.getElementById("loading");
    if (!el || el.classList.contains("hidden")) return false;
    const txt = ((el.querySelector(".loading-text") || {}).textContent || "");
    if (/Prontera|普隆德拉|Guardando|Saving|Cargando assets|Ragnarok/i.test(txt)) return false;
    return /Entrando en |Entering |進入/.test(txt);
  }
  const FARM_WALK_KEEP = new Set([
    "stages", "npc-dialog", "drop-reveal", "picker", "gameover",
    "charselect", "charcreate", "splash", "pause",
  ]);
  function farmClearWalkBlockers() {
    hideFarmNext();
    farmClosePlayerMenu();
    if (farmPlazaReady() && farmOverlayOpen("loading") && !farmLoadingEntersStage()) {
      document.getElementById("loading").classList.add("hidden");
    }
    for (const el of document.querySelectorAll(".overlay:not(.hidden)")) {
      if (!el || FARM_WALK_KEEP.has(el.id)) continue;
      if (el.id === "loading" && farmLoadingEntersStage()) continue;
      if (el.id && el.id.startsWith("ros-") && el.id !== "ros-farm-next") continue;
      el.classList.add("hidden");
      if (el.id === "ros-farm-next") el.classList.remove("overlay");
    }
  }
  function farmWalkToNpc(lobby, npc) {
    const s = lobby && lobby.player;
    if (!s || !npc) return false;
    lobby.talkTo = npc;
    const dist = Math.hypot(s.x - npc.x, s.y - npc.y) || 1;
    const stand = Math.min(dist, 102);
    let e = npc.x + (s.x - npc.x) / dist * stand;
    let t = npc.y + (s.y - npc.y) / dist * stand;
    try { if (typeof lobby.inPlaza === "function") [e, t] = lobby.inPlaza(e, t); } catch (_) {}
    try {
      if (lobby.walk && typeof lobby.walk.nearestWalkable === "function") {
        [e, t] = lobby.walk.nearestWalkable(e, t);
        lobby.movePath = typeof lobby.walk.pathTo === "function" ? lobby.walk.pathTo(s.x, s.y, e, t) : [{ x: e, y: t }];
      } else lobby.movePath = [{ x: e, y: t }];
    } catch (_) { lobby.movePath = [{ x: e, y: t }]; }
    return !!(lobby.movePath && lobby.movePath.length);
  }
  function farmCaptainNpc(lobby) {
    if (!lobby || !Array.isArray(lobby.npcs)) return null;
    return lobby.npcs.find((n) => n && (n.id === "captain" || FARM_CAPTAIN.some((s) => String(n.name || "").includes(s)))) || null;
  }
  function farmClosePlayerMenu() {
    const lobby = lobbyPlaza();
    if (lobby && typeof lobby.closeMenu === "function" && lobby.menu) {
      try { lobby.closeMenu(); return true; } catch (_) {}
    }
    const m = document.getElementById("player-menu");
    if (m) { m.remove(); return true; }
    return false;
  }
  const FARM_CAPTAIN = ["遠征隊長", "Capitán de expediciones", "Expedition Captain", "Capitão de Expedições"];
  const FARM_TALK = ["與隊長交談", "Hablar con el capitán", "Talk to the captain", "Falar com o capitão"];
  const FARM_DIFF = ["難度", "Dificultad", "Difficulty", "Dificuldade"];
  const FARM_MID = ["未完成的一局", "Partida a medias", "Unfinished run", "Partida inacabada"];
  const FARM_DISCARD = ["捨棄", "Descartar", "Discard"];
  const FARM_FIELD = ["前往野外", "Ir al campo", "Go to the field", "Ir para o campo"];
  const FARM_LOBBY_OFFLINE = [
    "Jugar sin conexión", "Play offline", "離線遊玩", "離線進行", "Jogar sem conexão", "Jogar offline",
    "Cancelar", "Cancel", "取消", "Cerrar", "Close", "關閉", "Fechar",
  ];
  const DIFF_KEY = "ro-survivors.difficulty.v1";
  const DIFF_OPTS = [
    { key: "count", min: 1, max: 3, soloMax: 3.5, names: { "zh-TW": "敵人數量", en: "Number of enemies", es: "Número de enemigos", "pt-BR": "Número de inimigos" } },
    { key: "damage", min: 1, max: 1.5, soloMax: 1.75, names: { "zh-TW": "敵人傷害", en: "Enemy damage", es: "Daño de los enemigos", "pt-BR": "Dano dos inimigos" } },
    { key: "hp", min: 1, max: 2, soloMax: 2.5, names: { "zh-TW": "敵人血量", en: "Enemy health", es: "Vida de los enemigos", "pt-BR": "HP dos inimigos" } },
    { key: "speed", min: 1, max: 1.5, soloMax: 1.75, names: { "zh-TW": "敵人速度", en: "Enemy speed", es: "Velocidad de los enemigos", "pt-BR": "Velocidade dos inimigos" } },
    { key: "events", min: 1, max: 2, soloMax: 2.5, names: { "zh-TW": "事件數量", en: "Number of events", es: "Número de eventos", "pt-BR": "Número de eventos" } },
  ];
  function clampDifficulty(raw, solo = true) {
    const src = raw && typeof raw === "object" ? raw : {};
    const out = {};
    for (const s of DIFF_OPTS) {
      const n = Number(src[s.key]);
      const cap = solo ? s.soloMax : s.max;
      out[s.key] = Number.isFinite(n) ? Math.min(cap, Math.max(s.min, n)) : s.min;
    }
    if (src.pick !== undefined) out.pick = src.pick;
    return out;
  }
  function loadDifficulty() {
    try { return clampDifficulty(JSON.parse(localStorage.getItem(DIFF_KEY) || "null")); }
    catch (_) { return clampDifficulty(null); }
  }
  function saveDifficulty(d) {
    try { localStorage.setItem(DIFF_KEY, JSON.stringify(clampDifficulty(d))); } catch (_) {}
  }
  function diffLootMul(a) {
    const e = 1 / DIFF_OPTS.length;
    let t = 1;
    for (const s of DIFF_OPTS) {
      const n = a[s.key];
      t += e * (Math.min(n, s.max) - s.min) / (s.max - s.min);
      if (n > s.max) t += e * 0.5 * (Math.min(n, s.soloMax) - s.max) / (s.soloMax - s.max);
    }
    return t;
  }
  function diffLootText(a) {
    return `×${(Math.round(diffLootMul(a) * 100) / 100).toFixed(2)}`;
  }
  function farmApplyDifficulty(dlg) {
    if (!dlg) return;
    const d = loadDifficulty();
    const root = dlg.querySelector(".diff") || dlg;
    for (const opt of DIFF_OPTS) {
      const inp = root.querySelector(`input[data-key="${opt.key}"]`);
      if (!inp) continue;
      const max = Number(inp.max);
      const cap = Number.isFinite(max) ? max : opt.soloMax;
      const val = Math.min(cap, Math.max(opt.min, d[opt.key]));
      if (Number(inp.value) === val) continue;
      inp.value = String(val);
      inp.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }
  let farmDiffOpen = false;
  let farmDiffOpenedAt = 0;
  function farmDiffEls() {
    const row = document.querySelector("#ros-plan-ov .ros-farm-opt:not(.ros-move-opt)");
    return { row, float: row && row.querySelector(".ros-farm-diff-float") };
  }
  function placeFarmDiffFloat() {
    const { row, float } = farmDiffEls();
    if (!row || !float) return;
    const r = row.getBoundingClientRect();
    float.style.left = r.left + "px";
    float.style.width = r.width + "px";
    const open = farmDiffOpen || row.classList.contains("ros-open");
    float.style.top = (open ? r.bottom - 1 : r.bottom) + "px";
  }
  function farmDiffInnerHeight() {
    const { float } = farmDiffEls();
    const inner = float && float.querySelector(".ros-farm-diff");
    return inner ? inner.scrollHeight : 0;
  }
  function setFarmDiffOpen(open) {
    const { row, float } = farmDiffEls();
    if (!row || !float) {
      farmDiffOpen = !!open;
      return;
    }
    placeFarmDiffFloat();
    if (open) {
      if (moveDropOpen) setMoveDropOpen(false);
      farmDiffOpenedAt = performance.now();
      if (farmDiffOpen && float.classList.contains("ros-open") && parseFloat(float.style.height) > 0) {
        float.style.height = farmDiffInnerHeight() + "px";
        return;
      }
      farmDiffOpen = true;
      row.classList.add("ros-open");
      float.classList.add("ros-open");
      float.style.height = "0px";
      float.offsetHeight;
      float.style.height = farmDiffInnerHeight() + "px";
    } else {
      if (!farmDiffOpen && !float.classList.contains("ros-open")) {
        float.style.height = "0px";
        return;
      }
      farmDiffOpen = false;
      const h = float.getBoundingClientRect().height || farmDiffInnerHeight();
      float.style.height = h + "px";
      float.offsetHeight;
      float.style.height = "0px";
      const onEnd = (e) => {
        if (e && e.propertyName && e.propertyName !== "height") return;
        if (!farmDiffOpen) {
          float.classList.remove("ros-open");
          row.classList.remove("ros-open");
        }
        float.removeEventListener("transitionend", onEnd);
      };
      float.addEventListener("transitionend", onEnd);
    }
  }
  function syncFarmDiffFloat() {
    const { row, float } = farmDiffEls();
    if (!row || !float) return;
    float.style.transition = "none";
    placeFarmDiffFloat();
    if (farmDiffOpen) {
      row.classList.add("ros-open");
      float.classList.add("ros-open");
      float.style.height = farmDiffInnerHeight() + "px";
    } else {
      float.style.height = "0px";
      float.classList.remove("ros-open");
      row.classList.remove("ros-open");
    }
    float.offsetHeight;
    float.style.transition = "";
  }
  let moveDropOpen = false;
  let moveDropOpenedAt = 0;
  function moveDropEls() {
    const row = document.querySelector("#ros-plan-ov .ros-move-opt");
    return { row, float: row && row.querySelector(".ros-move-drop-float") };
  }
  function placeMoveDropFloat() {
    const { row, float } = moveDropEls();
    if (!row || !float) return;
    const r = row.getBoundingClientRect();
    float.style.left = r.left + "px";
    float.style.width = r.width + "px";
    const open = moveDropOpen || row.classList.contains("ros-open");
    float.style.top = (open ? r.bottom - 1 : r.bottom) + "px";
  }
  function moveDropInnerHeight() {
    const { float } = moveDropEls();
    const inner = float && float.querySelector(".ros-move-drop-inner");
    return inner ? inner.scrollHeight : 0;
  }
  function setMoveDropOpen(open) {
    const { row, float } = moveDropEls();
    if (!row || !float) {
      moveDropOpen = !!open;
      return;
    }
    placeMoveDropFloat();
    if (open) {
      if (farmDiffOpen) setFarmDiffOpen(false);
      moveDropOpenedAt = performance.now();
      if (moveDropOpen && float.classList.contains("ros-open") && parseFloat(float.style.height) > 0) {
        float.style.height = moveDropInnerHeight() + "px";
        return;
      }
      moveDropOpen = true;
      row.classList.add("ros-open");
      float.classList.add("ros-open");
      float.style.height = "0px";
      float.offsetHeight;
      float.style.height = moveDropInnerHeight() + "px";
    } else {
      if (!moveDropOpen && !float.classList.contains("ros-open")) {
        float.style.height = "0px";
        return;
      }
      moveDropOpen = false;
      const h = float.getBoundingClientRect().height || moveDropInnerHeight();
      float.style.height = h + "px";
      float.offsetHeight;
      float.style.height = "0px";
      const onEnd = (e) => {
        if (e && e.propertyName && e.propertyName !== "height") return;
        if (!moveDropOpen) {
          float.classList.remove("ros-open");
          row.classList.remove("ros-open");
        }
        float.removeEventListener("transitionend", onEnd);
      };
      float.addEventListener("transitionend", onEnd);
    }
  }
  function syncMoveDropFloat() {
    const { row, float } = moveDropEls();
    if (!row || !float) return;
    float.style.transition = "none";
    placeMoveDropFloat();
    if (moveDropOpen) {
      row.classList.add("ros-open");
      float.classList.add("ros-open");
      float.style.height = moveDropInnerHeight() + "px";
    } else {
      float.style.height = "0px";
      float.classList.remove("ros-open");
      row.classList.remove("ros-open");
    }
    float.offsetHeight;
    float.style.transition = "";
  }
  document.addEventListener("pointerdown", (e) => {
    const t = e.target;
    const now = performance.now();
    if (farmDiffOpen && now - farmDiffOpenedAt > 80 && !(t && t.closest && t.closest("#ros-plan-ov .ros-farm-opt:not(.ros-move-opt)"))) {
      setFarmDiffOpen(false);
    }
    if (moveDropOpen && now - moveDropOpenedAt > 80 && !(t && t.closest && t.closest("#ros-plan-ov .ros-move-opt"))) {
      setMoveDropOpen(false);
    }
  }, true);
  document.addEventListener("scroll", () => {
    if (farmDiffOpen) placeFarmDiffFloat();
    if (moveDropOpen) placeMoveDropFloat();
  }, true);
  window.addEventListener("resize", () => {
    if (farmDiffOpen) placeFarmDiffFloat();
    if (moveDropOpen) placeMoveDropFloat();
  });
  function farmTryPickLobby() {
    const dlg = document.getElementById("npc-dialog");
    if (!dlg || dlg.classList.contains("hidden")) return false;
    const rows = [...dlg.querySelectorAll("#npc-text [data-lb], #npc-text button.ch-row.lb, #npc-text .lb-pick button")];
    if (!rows.length) return false;
    const free = rows.filter((b) => !b.disabled && !b.hasAttribute("disabled") && !b.classList.contains("full"));
    if (free.length) {
      const pick = free.find((b) => b.classList.contains("me")) || free[Math.floor(Math.random() * free.length)];
      pick.click();
      return true;
    }
    if (farmClickLabeled(dlg, FARM_LOBBY_OFFLINE)) return true;
    const opt = [...(dlg.querySelectorAll("#npc-options button") || [])].find((b) => !b.disabled);
    if (!opt) return false;
    opt.click();
    return true;
  }
  function farmDialogTitle() {
    if (!farmOverlayOpen("npc-dialog")) return "";
    return ((document.getElementById("npc-name") || {}).textContent || "").trim();
  }
  function farmClickLabeled(root, labels) {
    if (!root) return false;
    const want = labels instanceof Set ? labels : new Set(labels);
    const btns = [...root.querySelectorAll("button")];
    const hit = btns.find((b) => want.has((b.textContent || "").trim()));
    if (!hit || hit.disabled) return false;
    hit.click();
    return true;
  }
  function closeDropReveal() {
    const box = document.getElementById("drop-reveal");
    if (!box || box.classList.contains("hidden")) { farmRevealAt = 0; return false; }
    if (!farmRevealAt) farmRevealAt = performance.now();
    if (performance.now() - farmRevealAt < 650) return false;
    if (box.classList.contains("roll")) {
      const parsed = parseDropReveal();
      let match = false;
      if (parsed && parsed.kind === "equip") match = !!equipWantedMatch(parsed, true);
      else if (parsed && parsed.kind === "card") match = (store.farm.cards || []).some((x) => Number(x) === Number(parsed.id));
      else if (parsed && parsed.kind === "egg" && parsed.pet) match = (store.farm.pets || []).includes(parsed.pet.id);
      const btn = box.querySelector(match ? "[data-c=need]" : "[data-c=greed]") || box.querySelector("[data-c=need]");
      if (btn && !btn.disabled) { btn.click(); return true; }
    }
    const get = box.querySelector("button.dr-get, .dr-get");
    if (get && !get.disabled) { get.click(); return true; }
    return false;
  }
  const FARM_WASD = ["w", "a", "s", "d"];
  const FARM_KEY_ALL = ["w", "a", "s", "d", "arrowup", "arrowdown", "arrowleft", "arrowright"];
  let farmKeyTimer = 0;
  const farmHeldKeys = new Set();
  function farmKeyCode(k) {
    return ({ w: "KeyW", a: "KeyA", s: "KeyS", d: "KeyD" })[k] || k;
  }
  function farmDispatchKey(type, k) {
    try {
      window.dispatchEvent(new KeyboardEvent(type, {
        key: k, code: farmKeyCode(k), bubbles: true, cancelable: true,
      }));
    } catch (_) {}
  }
  function farmReleaseHeldKeys() {
    for (const k of [...farmHeldKeys]) farmDispatchKey("keyup", k);
    farmHeldKeys.clear();
  }
  function farmHoldKeys(names) {
    const want = new Set(names);
    for (const k of [...farmHeldKeys]) {
      if (!want.has(k)) { farmDispatchKey("keyup", k); farmHeldKeys.delete(k); }
    }
    for (const k of want) {
      farmDispatchKey("keydown", k);
      farmHeldKeys.add(k);
    }
  }
  function farmSteerTouch(lobby, names) {
    if (!lobby || !lobby.touchMove || typeof lobby.touchMove !== "object") return;
    let x = 0, y = 0;
    if (names.includes("a")) x -= 1;
    if (names.includes("d")) x += 1;
    if (names.includes("w")) y -= 1;
    if (names.includes("s")) y += 1;
    const len = Math.hypot(x, y) || 1;
    lobby.touchMove.x = x ? x / len : 0;
    lobby.touchMove.y = y ? y / len : 0;
  }
  function farmApplyKeys(lobby, names) {
    const ks = lobby && lobby.keys;
    if (ks && typeof ks.add === "function" && typeof ks.delete === "function") {
      for (const k of FARM_KEY_ALL) {
        if (names.includes(k)) ks.add(k);
        else ks.delete(k);
      }
    }
    farmSteerTouch(lobby, names);
    farmHoldKeys(names);
    farmWalking = true;
  }
  let farmWalking = false;
  function farmStopKeyWalk() {
    if (!farmKeyTimer && !farmHeldKeys.size && !farmWalking) return;
    if (farmKeyTimer) { clearInterval(farmKeyTimer); farmKeyTimer = 0; }
    const lobby = lobbyPlaza() || livePlaza;
    if (lobby && lobby.keys && typeof lobby.keys.delete === "function") {
      for (const k of farmHeldKeys) lobby.keys.delete(k);
    }
    if (farmWalking) farmSteerTouch(lobby, []);
    farmReleaseHeldKeys();
    farmWalking = false;
  }
  function farmChatTyping() {
    const ae = document.activeElement;
    if (!ae) return false;
    const tag = (ae.tagName || "").toLowerCase();
    return tag === "input" || tag === "textarea" || ae.isContentEditable;
  }
  function farmTalkCaptain(lobby, npc) {
    farmApplyKeys(lobby, []);
    const prompt = document.getElementById("lobby-prompt");
    if (prompt && !prompt.classList.contains("hidden")) {
      const txt = (prompt.textContent || "").trim();
      if (FARM_TALK.some((s) => txt.includes(s))) { prompt.click(); return true; }
    }
    if (npc && typeof npc.onTalk === "function") {
      try { npc.onTalk(); return true; } catch (_) {}
    }
    if (lobby && lobby.near && typeof lobby.near.onTalk === "function") {
      try { lobby.near.onTalk(); return true; } catch (_) {}
    }
    farmDispatchKey("keydown", " ");
    farmDispatchKey("keyup", " ");
    return false;
  }
  function farmStepKeyWalk() {
    if (!store.farm || !store.farm.enabled || !farmNextDone || !document.body.classList.contains("in-lobby")) {
      farmStopKeyWalk();
      return;
    }
    if (farmOverlayOpen("stages") || (farmOverlayOpen("loading") && farmLoadingEntersStage())) {
      farmStopKeyWalk();
      return;
    }
    farmClearWalkBlockers();
    try { if (typeof lobbyPlaza().menuOpen === "function" && lobbyPlaza().menuOpen()) farmCloseWindows(); } catch (_) {}
    const lobby = lobbyPlaza();
    const npc = farmCaptainNpc(lobby);
    if (!lobby || !npc || !lobby.player) return;
    if (farmChatTyping()) { farmApplyKeys(lobby, []); return; }
    const px = lobby.player.x, py = lobby.player.y;
    if (!Number.isFinite(px) || !Number.isFinite(py) || !Number.isFinite(npc.x) || !Number.isFinite(npc.y)) {
      farmApplyKeys(lobby, []);
      return;
    }
    const dist = Math.hypot(px - npc.x, py - npc.y);
    if (dist < 170) { farmTalkCaptain(lobby, npc); return; }
    const dx = npc.x - px, dy = npc.y - py;
    const names = [];
    if (dx < -12) names.push("a");
    if (dx > 12) names.push("d");
    if (dy < -12) names.push("w");
    if (dy > 12) names.push("s");
    farmApplyKeys(lobby, names);
  }
  function farmStartKeyWalk() {
    farmStepKeyWalk();
    if (!farmKeyTimer && store.farm && store.farm.enabled && farmNextDone) {
      farmKeyTimer = setInterval(farmStepKeyWalk, 80);
    }
  }
  function farmTryCaptain() {
    farmStartKeyWalk();
    const lobby = lobbyPlaza();
    return !!(lobby && farmCaptainNpc(lobby));
  }
  function farmSelectStage(stageId) {
    const list = document.getElementById("stg-list");
    if (!list) return false;
    const names = new Set();
    const st = DATA.farm.stages.find((s) => s.id === stageId);
    if (st && st.names) Object.values(st.names).forEach((n) => n && names.add(n));
    const cards = [...list.querySelectorAll(".stg-card")];
    let card = cards.find((b) => names.has(((b.querySelector("b") || {}).textContent || "").trim()));
    if (!card) {
      const i = DATA.farm.stages.findIndex((s) => s.id === stageId);
      if (i >= 0) card = list.querySelector(`.stg-card[data-i="${i}"]`);
    }
    if (!card) return false;
    if (!card.classList.contains("sel")) { card.click(); return true; }
    const go = document.getElementById("stg-go");
    if (!go || go.disabled || go.classList.contains("hidden") || card.classList.contains("locked") || card.classList.contains("soon")) {
      if (farmLockToast !== stageId) {
        farmLockToast = stageId;
        toast(L("farmLocked"));
      }
      return false;
    }
    go.click();
    return true;
  }
  function farmTick() {
    try { applyPartyTowerGate(); } catch (_) {}
    if (featuresBlocked()) return;
    farmNoteLobby(document.body.classList.contains("in-lobby"));
    if (!store.farm) store.farm = defaultFarm();
    if (!planUnlocked()) { hideFarmNext(); if (farmKeyTimer || farmHeldKeys.size || farmWalking) farmStopKeyWalk(); return; }
    if (!store.farm.enabled) { hideFarmNext(); if (farmKeyTimer || farmHeldKeys.size || farmWalking) farmStopKeyWalk(); return; }
    syncFarmSig();
    if (!farmHasTargets()) { hideFarmNext(); return; }
    scanFarmDrops();
    if (closeDropReveal()) { farmActAt = performance.now(); return; }
    if (farmAllDone()) { hideFarmNext(); return; }
    const now = performance.now();
    if (now - farmActAt < 700) return;
    if (farmOverlayOpen("drop-reveal")) return;
    if (farmOverlayOpen("picker")) return;
    if (farmOverlayOpen("loading") && !(farmPlazaReady() && !farmLoadingEntersStage() && farmNextDone)) return;
    const inLobby = document.body.classList.contains("in-lobby");
    if (inLobby && farmAwaitNextRun()) return;
    const title = farmDialogTitle();
    if (title && FARM_MID.some((s) => title.includes(s))) {
      if (farmClickLabeled(document.getElementById("npc-dialog"), FARM_DISCARD)) farmActAt = now;
      return;
    }
    if (title && FARM_DIFF.some((s) => title.includes(s))) {
      const dlg = document.getElementById("npc-dialog");
      farmApplyDifficulty(dlg);
      if (farmClickLabeled(dlg, FARM_FIELD)) farmActAt = now;
      return;
    }
    if (farmTryPickLobby()) { farmActAt = now; return; }
    if (farmOverlayOpen("gameover")) {
      const btn = document.getElementById("btn-restart");
      if (btn && !btn.disabled) { btn.click(); farmActAt = now; }
      return;
    }
    if (farmOverlayOpen("pause")) {
      if (farmClickId("btn-resume")) farmActAt = now;
      return;
    }
    if (!inLobby) return;
    if (farmCloseWindows()) { farmActAt = now; return; }
    if (farmOverlayOpen("stages")) {
      const stageId = pickFarmStage();
      if (!stageId) {
        if (farmLockToast !== "none") { farmLockToast = "none"; toast(L("farmNoStage")); }
        return;
      }
      if (farmSelectStage(stageId)) farmActAt = now;
      return;
    }
    if (title && farmDismissDialog()) { farmActAt = now; return; }
    if (farmTryCaptain()) farmActAt = now;
  }


  function farmActiveTarget() {
    const f = store.farm;
    if (f.equip && f.equip[0]) return { kind: "equip", id: f.equip[0].id, minQuality: f.equip[0].minQuality || 0, affixes: f.equip[0].affixes || [] };
    if (f.cards && f.cards[0] != null) return { kind: "cards", id: f.cards[0] };
    if (f.pets && f.pets[0]) return { kind: "pets", id: f.pets[0] };
    return null;
  }
  function isFarmTarget(kind, id) {
    const t = farmActiveTarget();
    return !!(t && t.kind === kind && String(t.id) === String(id));
  }
  function clearFarmTargets() {
    store.farm.equip = [];
    store.farm.cards = [];
    store.farm.pets = [];
  }
  function setFarmTarget(kind, payload) {
    clearFarmTargets();
    if (kind === "equip") store.farm.equip = [payload];
    else if (kind === "cards") store.farm.cards = [payload];
    else store.farm.pets = [payload];
    resetFarmProgress();
    saveStore();
  }
  function removeFarmTarget() {
    clearFarmTargets();
    farmSel = null;
    farmDraft = null;
    resetFarmProgress();
    saveStore();
  }
  function farmItemIcon(kind, it) {
    if (!it) return "";
    if (kind === "equip") return `/assets/items/${it.id}.png`;
    if (kind === "cards") return `/assets/cards/${it.id}.png`;
    return `/assets/items/${it.egg}.png`;
  }
  function farmStagesText(it) {
    if (!it || !it.stages || !it.stages.length) return "";
    return it.stages.map((sid) => farmLang((DATA.farm.stages.find((s) => s.id === sid) || {}).names, sid)).join(" · ");
  }
  function ensureFarmDraft(kind, id) {
    if (farmDraft && farmDraft.kind === kind && String(farmDraft.id) === String(id)) return farmDraft;
    if (kind === "equip" && isFarmTarget(kind, id)) {
      const w = (store.farm.equip || [])[0] || {};
      farmDraft = { kind, id, minQuality: w.minQuality || 0, affixes: (w.affixes || []).slice() };
    } else {
      farmDraft = { kind, id, minQuality: 0, affixes: [] };
    }
    return farmDraft;
  }
  function farmCellClass(kind, it, committed, picking) {
    const cls = ["item-cell"];
    if (kind === "cards") cls.push("card-cell");
    if (kind === "pets") cls.push("pet-cell");
    if (it && it.rare) cls.push("rare");
    if (committed) {
      cls.push("sel");
      if (kind === "equip") {
        const t = farmActiveTarget();
        if (t && t.minQuality) cls.push("q" + t.minQuality);
      }
    } else if (picking) cls.push("ros-picking");
    return cls.join(" ");
  }
  function renderFarmTargetCard() {
    const t = farmActiveTarget();
    const box = el("div", { class: "ros-farm-target" + (t ? "" : " empty") });
    if (!t) {
      const meta = el("div", { class: "ros-farm-target-meta" });
      meta.appendChild(el("b", null, L("farmTarget")));
      meta.appendChild(el("div", { class: "ros-muted" }, L("farmNoTarget")));
      meta.appendChild(el("div", { class: "ros-muted" }, L("farmHint")));
      box.appendChild(meta);
      return box;
    }
    const it = farmCatalog(t.kind, t.id);
    const row = el("div", { class: "ros-farm-target-row" });
    const cell = el("div", { class: farmCellClass(t.kind, it, true, false) });
    if (it) cell.appendChild(el("img", { src: farmItemIcon(t.kind, it), alt: "" }));
    cell.appendChild(el("span", { class: "ros-farm-mark" }, L("picked")));
    row.appendChild(cell);
    const meta = el("div", { class: "ros-farm-target-meta" });
    meta.appendChild(el("b", null, it ? it.name : String(t.id)));
    const kindLab = t.kind === "equip" ? L("equip") : t.kind === "cards" ? L("cards") : L("pets");
    const bits = [L("farmTarget"), kindLab];
    const st = farmStagesText(it);
    if (st) bits.push(st);
    else if (t.kind === "pets" && it && it.obtain === "evolution") bits.push(L("farmEvo"));
    if (t.kind === "equip") {
      const q = (DATA.farm.qualities || []).find((x) => x.id === (t.minQuality || 0));
      if (q && t.minQuality) bits.push(L("minQuality") + " " + farmLang(q.names, q.id));
      if (t.affixes && t.affixes.length) {
        const names = t.affixes.map((id) => {
          const a = (DATA.farm.affixes || []).find((x) => x.id === id);
          return farmLang(a && a.names, id);
        }).join(" · ");
        bits.push(names);
      }
    }
    meta.appendChild(el("div", { class: "ros-muted" }, bits.join(" · ")));
    row.appendChild(meta);
    const rm = el("button", { class: "ro-btn", type: "button" }, L("remove"));
    rm.addEventListener("click", () => { removeFarmTarget(); renderWindow(); });
    row.appendChild(rm);
    box.appendChild(row);
    return box;
  }

  function renderFarmPreview(kind, it, detail) {
    const committed = isFarmTarget(kind, it.id);
    const draft = kind === "equip" ? ensureFarmDraft(kind, it.id) : null;
    detail.appendChild(el("div", { class: "ros-sec-title" }, it.name));
    const st = farmStagesText(it);
    if (st) detail.appendChild(el("div", { class: "ros-muted" }, st));
    else if (kind === "pets" && it.obtain === "evolution") detail.appendChild(el("div", { class: "ros-muted" }, L("farmEvo")));
    if (kind === "equip") {
      detail.appendChild(el("div", { class: "ros-sec-title" }, L("minQuality")));
      const qs = el("div", { class: "inv-filters" });
      for (const q of DATA.farm.qualities) {
        const b = el("button", { class: "inv-chip q-chip" + (draft.minQuality === q.id ? " active" : ""), type: "button" }, farmLang(q.names, q.id));
        b.style.setProperty("--q", q.color);
        b.addEventListener("click", () => {
          draft.minQuality = q.id;
          if (committed) {
            store.farm.equip[0].minQuality = q.id;
            resetFarmProgress();
            saveStore();
          }
          renderWindow();
        });
        qs.appendChild(b);
      }
      detail.appendChild(qs);
      detail.appendChild(el("div", { class: "ros-sec-title" }, L("affixes")));
      for (const a of DATA.farm.affixes) {
        const on = (draft.affixes || []).includes(a.id);
        const sw = optSwitch(farmLang(a.names, a.id), on, (v) => {
          draft.affixes = draft.affixes || [];
          if (v && !draft.affixes.includes(a.id)) draft.affixes.push(a.id);
          if (!v) draft.affixes = draft.affixes.filter((x) => x !== a.id);
          if (committed) {
            store.farm.equip[0].affixes = draft.affixes.slice();
            resetFarmProgress();
            saveStore();
          }
        });
        detail.appendChild(sw);
      }
    }
    if (committed) {
      detail.appendChild(el("div", { class: "ros-muted" }, L("picked") + " · " + L("farmTarget")));
    } else {
      const add = el("button", { class: "ro-btn primary", type: "button" }, L("add"));
      add.addEventListener("click", () => {
        if (kind === "equip") {
          setFarmTarget("equip", { id: it.id, minQuality: (draft && draft.minQuality) || 0, affixes: ((draft && draft.affixes) || []).slice() });
        } else if (kind === "cards") setFarmTarget("cards", Number(it.id));
        else setFarmTarget("pets", it.id);
        farmSel = { kind, id: it.id };
        renderWindow();
      });
      detail.appendChild(add);
    }
  }

  function renderFarmStageRow() {
    const row = el("div", { class: "inv-filters ros-farm-stages" });
    const auto = el("button", { class: "inv-chip" + (farmIsAutoStage() ? " active" : ""), type: "button" }, L("farmAuto"));
    auto.addEventListener("click", () => { store.farm.stage = "auto"; saveStore(); renderWindow(); });
    row.appendChild(auto);
    for (const s of farmableStages()) {
      const b = el("button", { class: "inv-chip" + (store.farm.stage === s.id ? " active" : ""), type: "button" }, farmLang(s.names, s.id));
      b.addEventListener("click", () => { store.farm.stage = s.id; saveStore(); renderWindow(); });
      row.appendChild(b);
    }
    return row;
  }
  function renderFarmDetailEmpty() {
    return el("div", { class: "browse-detail" }, `<div class="ros-sec-title">${L("farmHint")}</div>`);
  }
  function renderEquipTab() {
    const box = el("div", { class: "ros-farm-layout" });
    const listBox = el("div", { class: "inv-box" });
    const filters = el("div", { class: "inv-filters" });
    for (const f of DATA.farm.filters) {
      const b = el("button", { class: "inv-chip" + (farmFilter === f.id ? " active" : ""), type: "button" }, farmLang(f.names, f.id));
      b.addEventListener("click", () => { farmFilter = f.id; renderWindow(); });
      filters.appendChild(b);
    }
    listBox.appendChild(filters);
    const grid = el("div", { class: "item-grid" });
    const filt = DATA.farm.filters.find((f) => f.id === farmFilter);
    let shown = 0;
    for (const it of DATA.farm.equip) {
      if (!farmItemVisible("equip", it)) continue;
      if (filt && filt.slots && !filt.slots.includes(it.slot)) continue;
      shown++;
      const committed = isFarmTarget("equip", it.id);
      const picking = !!(farmSel && farmSel.kind === "equip" && farmSel.id === it.id);
      const cell = el("button", { class: farmCellClass("equip", it, committed, picking), type: "button", title: it.name });
      cell.appendChild(el("img", { src: farmItemIcon("equip", it), alt: "" }));
      if (committed) cell.appendChild(el("span", { class: "ros-farm-mark" }, L("picked")));
      cell.addEventListener("click", () => {
        farmSel = { kind: "equip", id: it.id };
        ensureFarmDraft("equip", it.id);
        renderWindow();
      });
      grid.appendChild(cell);
    }
    if (!shown) grid.appendChild(el("div", { class: "ros-muted empty-note" }, farmMissingOnly() ? L("farmNoMissing") : L("farmStageEmpty")));
    listBox.appendChild(grid);
    box.appendChild(listBox);
    const detail = el("div", { class: "browse-detail" });
    const it = farmSel && farmSel.kind === "equip" ? farmCatalog("equip", farmSel.id) : null;
    const itOk = it && farmItemVisible("equip", it);
    if (itOk) renderFarmPreview("equip", it, detail);
    else detail.appendChild(el("div", { class: "ros-muted" }, L("farmNoTarget")));
    box.appendChild(detail);
    return box;
  }
  function renderIdTab(kind) {
    const isCard = kind === "cards";
    const box = el("div", { class: "ros-farm-layout" });
    const listBox = el("div", { class: "inv-box" });
    if (isCard) {
      const filters = el("div", { class: "inv-filters" });
      for (const f of DATA.farm.cardFilters) {
        const b = el("button", { class: "inv-chip" + (farmCardFilter === f.id ? " active" : ""), type: "button" }, farmLang(f.names, f.id));
        b.addEventListener("click", () => { farmCardFilter = f.id; renderWindow(); });
        filters.appendChild(b);
      }
      listBox.appendChild(filters);
    }
    const grid = el("div", { class: "item-grid" });
    const rows = isCard ? DATA.farm.cards : farmPetsList();
    let shown = 0;
    for (const it of rows) {
      if (!isCard && it.obtain === "evolution") continue;
      if (!farmItemVisible(kind, it)) continue;
      if (isCard && farmCardFilter !== "all") {
        const f = DATA.farm.cardFilters.find((x) => x.id === farmCardFilter);
        if (f && f.slot && it.slot !== f.slot) continue;
      }
      shown++;
      const committed = isFarmTarget(kind, it.id);
      const picking = !!(farmSel && farmSel.kind === kind && String(farmSel.id) === String(it.id));
      const cell = el("button", {
        class: farmCellClass(kind, it, committed, picking),
        type: "button",
        title: it.name,
      });
      cell.appendChild(el("img", { src: farmItemIcon(kind, it), alt: "" }));
      if (committed) cell.appendChild(el("span", { class: "ros-farm-mark" }, L("picked")));
      cell.addEventListener("click", () => {
        farmSel = { kind, id: it.id };
        renderWindow();
      });
      grid.appendChild(cell);
    }
    if (!shown) grid.appendChild(el("div", { class: "ros-muted empty-note" }, farmMissingOnly() ? L("farmNoMissing") : L("farmStageEmpty")));
    listBox.appendChild(grid);
    box.appendChild(listBox);
    const detail = el("div", { class: "browse-detail" });
    const it = farmSel && farmSel.kind === kind ? farmCatalog(kind, farmSel.id) : null;
    const itOk = it && farmItemVisible(kind, it);
    if (itOk) renderFarmPreview(kind, it, detail);
    else detail.appendChild(el("div", { class: "ros-muted" }, L("farmNoTarget")));
    box.appendChild(detail);
    return box;
  }

  /* -------------------- UI -------------------- */
  const css = `
#ros-plan-btn{
  position:fixed; z-index:46; left:12px; bottom:12px;
  width:42px; height:42px; padding:6px; box-sizing:border-box;
  display:flex; align-items:center; justify-content:center;
  cursor:pointer; border-radius:11px; color:#fff;
  background:var(--ro-title, linear-gradient(180deg,#97b1e6 0%,#7d9ad6 45%,#5f7fc0 55%,#3a559a 100%));
  border:1px solid var(--ro-border,#6b7ba8);
  box-shadow:0 0 0 2px #ffffff59, 0 6px 16px #00000055;
}
#ros-plan-btn:hover{ filter:brightness(1.06); }
#ros-plan-btn img{ width:26px; height:26px; image-rendering:pixelated;
  background:var(--ro-slot,#eef2fa); border:1px solid var(--ro-slot-border,#8b96b8); border-radius:6px; padding:2px; }
#ros-plan-btn .ros-dot{ position:absolute; right:4px; top:4px; width:8px; height:8px; border-radius:50%;
  background:#8ee59a; box-shadow:0 0 6px #8ee59a; }
#ros-plan-btn .ros-dot.off{ background:#c9d0e0; box-shadow:none; }
#ros-plan-btn.ros-blocked{ cursor:not-allowed !important; filter:grayscale(.35) brightness(.92); }
#ros-plan-gate-text{ white-space:pre-line; text-align:center; }
#ros-plan-tip.tooltip{ position:fixed; z-index:48; max-width:270px; padding:8px 10px; pointer-events:none;
  line-height:1.45; font-size:var(--fs-sm,11px); font-family:Nunito,"Noto Sans TC",sans-serif;
  background:linear-gradient(#fff,#f1f4fb); color:var(--ro-text,#24304f);
  border:1px solid var(--ro-border,#6b7ba8); border-radius:10px; box-shadow:0 6px 18px #00000059; }
#lobby-chat, #run-chat{ left: calc(max(12px, env(safe-area-inset-left, 0px)) + 46px) !important; }

#ros-plan-ov .ro-btn,#ros-asp .ro-btn{font:inherit;font-weight:800;color:#2a3a6a;background:linear-gradient(#fff,#e2e8f7);border:1px solid #a3b2db;border-radius:10px;padding:7px 18px;margin:4px;cursor:pointer;box-shadow:0 2px #bcc7e6,inset 0 1px #fff;}
#ros-plan-ov .ro-btn.primary,#ros-asp .ro-btn.primary{color:#fff;background:linear-gradient(#a6c2f7,#6f92e0 50%,#4d6fbf);border-color:#2f4a8a;text-shadow:1px 1px 0 #1d2d57;box-shadow:0 2px #2f4a8a,inset 0 1px #ffffff8c;}
#ros-plan-ov.ros-plan-overlay, #ros-asp.ros-plan-overlay{
  position:fixed; top:0; right:0; bottom:0; left:0;
  z-index:45; display:flex; align-items:center; justify-content:center;
  background:rgba(12,18,36,.55); }
#ros-asp.ros-plan-overlay{ z-index:46; }
#ros-farm-next.overlay, #ros-plan-gate.overlay{ z-index:47; }
#ros-farm-next.hidden, #ros-plan-gate.hidden{ display:none !important; }
#ros-farm-next .btn-row.pad, #ros-plan-gate .btn-row.pad{ justify-content:center; }
#ros-plan-ov.hidden, #ros-asp.hidden{ display:none !important; }
#ros-plan-ov .ros-plan-window{ width:min(820px, calc(100vw - 24px)); max-height:calc(100vh - 24px);
  display:flex; flex-direction:column; font-family:Nunito, "Noto Sans TC", sans-serif; color:var(--ro-text,#24304f); }
#ros-asp .ros-asp-window{ width:min(420px, calc(100vw - 32px)); max-height:calc(100vh - 32px);
  display:flex; flex-direction:column; font-family:Nunito, "Noto Sans TC", sans-serif; color:var(--ro-text,#24304f); }
#ros-plan-ov .ro-body, #ros-asp .ro-body{ display:flex; flex-direction:column; gap:10px; min-height:0; flex:1; overflow:hidden; padding:12px 14px 10px; }
#ros-plan-ov .ro-title, #ros-asp .ro-title{ position:relative; display:flex; align-items:center; justify-content:center; gap:8px; }
#ros-plan-ov .ros-plan-ver{ font-size:calc(1em * 10 / 12); font-weight:700; }
#ros-plan-ov .ros-back{ position:absolute; left:10px; top:50%; transform:translateY(-50%);
  margin:0; padding:2px 8px; font-size:11px; font-weight:800; line-height:1.2;
  border-radius:7px; box-shadow:0 1px #bcc7e6,inset 0 1px #fff; }
#ros-plan-ov .ro-x, #ros-asp .ro-x{ position:absolute; right:8px; top:50%; transform:translateY(-50%);
  width:28px; height:28px; margin:0; padding:0; border:0; background:transparent; color:#fff;
  font:800 22px/1 Nunito,sans-serif; cursor:pointer; text-shadow:1px 1px 0 #1d2d57; }
.ros-opts{ display:flex; flex-direction:column; gap:8px; }
#ros-plan-ov .ros-subtabs, #ros-asp .ros-subtabs{ display:flex; gap:6px; flex-wrap:wrap; }
#ros-plan-ov .ros-subtabs .inv-chip, #ros-asp .ros-subtabs .inv-chip{ flex:1; min-width:70px; justify-content:center; text-align:center; }
#ros-asp .inv-filters{
  display:flex; flex-wrap:wrap; gap:8px; align-items:stretch;
}
#ros-asp .inv-filters .inv-chip{
  flex:1; min-width:70px; margin:0; justify-content:center; text-align:center;
}
#ros-asp .ros-subtabs + .inv-filters{ margin-top:10px; }
#ros-asp .ros-basic-order-row{ gap:10px; }
#ros-asp .ros-basic-order-row > span{ flex:1; min-width:0; }
#ros-asp .ros-basic-order-btns{ display:flex; align-items:center; gap:4px; flex:none; }
#ros-asp .ros-basic-order-btns .inv-chip{ flex:none; min-width:30px; padding:4px 8px; margin:0; justify-content:center; text-align:center; }
#ros-plan-ov .ros-build-panel, #ros-plan-ov .ros-farm-panel{ display:flex; flex-direction:column; gap:8px; min-height:0; }
#ros-plan-ov .opt-check, #ros-asp .opt-check{
  position:relative; display:flex; align-items:center; justify-content:center;
  flex:none; width:40px; height:22px; margin:0; padding:0; cursor:pointer;
}
#ros-plan-ov .opt-check input, #ros-asp .opt-check input{
  position:absolute; inset:0; margin:0; width:100%; height:100%;
  opacity:0; pointer-events:none; appearance:none;
}
#ros-plan-ov .opt-switch, #ros-asp .opt-switch{
  position:relative; flex:none; width:40px; height:22px; border-radius:11px;
  background:#c9d1e6; box-shadow:inset 0 1px 3px #24304f40; transition:background .15s;
}
#ros-plan-ov .opt-switch:after, #ros-asp .opt-switch:after{
  content:""; position:absolute; top:2px; left:2px; width:18px; height:18px;
  border-radius:50%; background:#fff; box-shadow:0 1px 3px #0000004d; transition:transform .15s;
}
#ros-plan-ov .opt-check input:checked + .opt-switch,
#ros-asp .opt-check input:checked + .opt-switch{ background:var(--ro-blue-2,#3a5bb4); }
#ros-plan-ov .opt-check input:checked + .opt-switch:after,
#ros-asp .opt-check input:checked + .opt-switch:after{ transform:translate(18px); }
#ros-plan-ov .ros-farm-opt,
#ros-plan-ov .ros-move-opt{
  position:relative; flex-direction:column; align-items:stretch; gap:0; cursor:pointer;
  overflow:visible; z-index:2;
  transition:border-radius .26s cubic-bezier(.22,.75,.25,1);
}
#ros-plan-ov .ros-farm-opt.ros-open,
#ros-plan-ov .ros-move-opt.ros-open{
  z-index:10;
  border-bottom-left-radius:0;
  border-bottom-right-radius:0;
  border-bottom-color:transparent;
}
#ros-plan-ov .ros-farm-opt-head,
#ros-plan-ov .ros-move-opt-head{ display:flex; align-items:center; gap:12px; }
#ros-plan-ov .ros-farm-opt-head>span:first-child,
#ros-plan-ov .ros-move-opt-head>span:first-child{ flex:1; min-width:0; display:flex; flex-direction:column; }
#ros-plan-ov .ros-farm-opt-head>span:first-child b:after,
#ros-plan-ov .ros-move-opt-head>span:first-child b:after{
  content:""; display:inline-block; margin-left:6px; vertical-align:middle;
  border:4px solid transparent; border-top-color:var(--ro-blue-3,#24418e);
  transform:translateY(2px); transition:transform .2s ease;
}
#ros-plan-ov .ros-farm-opt.ros-open .ros-farm-opt-head>span:first-child b:after,
#ros-plan-ov .ros-move-opt.ros-open .ros-move-opt-head>span:first-child b:after{
  transform:translateY(-1px) rotate(180deg);
}
#ros-plan-ov .ros-farm-diff-float,
#ros-plan-ov .ros-move-drop-float{
  position:fixed; z-index:8; box-sizing:border-box;
  height:0; overflow:hidden; pointer-events:none;
  background:#fff;
  border:1px solid var(--ro-line,#d3dbef);
  border-top:0;
  border-radius:0 0 12px 12px;
  box-shadow:none;
  transition:height .26s cubic-bezier(.22,.75,.25,1);
}
#ros-plan-ov .ros-farm-diff-float:not(.ros-open),
#ros-plan-ov .ros-move-drop-float:not(.ros-open){
  border-color:transparent;
  background:transparent;
  visibility:hidden;
}
#ros-plan-ov .ros-farm-diff-float.ros-open,
#ros-plan-ov .ros-move-drop-float.ros-open{ pointer-events:auto; }
#ros-plan-ov .ros-farm-diff, #ros-plan-ov .ros-move-drop-inner{ margin:0; padding:8px 12px 10px; border-top:1px solid var(--ro-line,#d3dbef); }
#ros-plan-ov .ros-move-drop-inner{ display:flex; flex-direction:column; gap:6px; }
#ros-plan-ov .ros-move-drop-inner .opt-row{ margin:0; padding:6px 10px; background:var(--ro-slot,#f4f7fd); }
.ros-tabs{ display:flex; gap:6px; flex-wrap:wrap; }
.ros-tabs .tab-btn{ flex:1; min-width:70px; padding:6px 8px; font-size:13px; }
.ros-muted{ font-size:12px; font-weight:700; color:var(--ro-muted,#6c7896); line-height:1.35; }
.ros-farm-stages{ margin:0; }
.ros-farm-layout{ display:grid; grid-template-columns:minmax(0,1fr) minmax(180px,240px); gap:10px; align-items:stretch; min-height:0; flex:1; }
#ros-plan-ov .ros-farm-layout .inv-box{ max-height:min(360px, 44vh); overflow:auto; }
#ros-plan-ov .ros-farm-layout .browse-detail{ position:sticky; top:0; max-height:min(360px, 44vh); overflow:auto; padding:2px 2px 8px; }
#ros-plan-ov button.item-cell{ padding:0; font:inherit; color:inherit; appearance:none; }
#ros-plan-ov .ros-farm-layout .opt-row{ margin:4px 0; }
#ros-plan-ov .item-cell.ros-picking{ border-color:var(--ro-blue-1,#6f8fd8); box-shadow:0 0 0 2px #6f8fd866; transform:translateY(-1px); }
#ros-plan-ov .item-cell.sel{
  border:2px solid var(--ro-blue-2,#3a5bb4);
  box-shadow:0 0 0 3px #3a5bb4aa, 0 0 10px #3a5bb466;
  background:linear-gradient(#e8f0ff,#c5d6f8);
}
#ros-plan-ov .item-cell.sel:is(.q1,.q2,.q3,.q4){ box-shadow:inset 0 0 8px var(--qg,transparent),0 0 0 3px #3a5bb4aa,0 0 10px #3a5bb466; }
#ros-plan-ov .item-cell .ros-farm-mark,
#ros-plan-ov .ros-chip .ros-farm-mark,
#ros-asp .ros-chip .ros-farm-mark{
  position:absolute; left:1px; top:1px; z-index:1;
  padding:0 3px; border-radius:4px;
  font-size:8px; font-weight:900; line-height:12px;
  color:#fff; background:var(--ro-blue-2,#3a5bb4);
  pointer-events:none;
}
#ros-plan-ov .ros-farm-target{
  display:flex; flex-direction:column; gap:4px;
  margin:0; padding:6px 8px;
  border-radius:10px;
  background:linear-gradient(#fbfcff,#e8effc);
  border:2px solid var(--ro-blue-2,#3a5bb4);
  box-shadow:0 0 0 2px #6f8fd866;
}
#ros-plan-ov .ros-farm-target.empty{ border-color:var(--ro-line,#d3dbef); box-shadow:none; background:linear-gradient(#fbfcff,#eef2fa); }
#ros-plan-ov .ros-farm-target-row{ display:flex; align-items:center; gap:10px; }
#ros-plan-ov .ros-farm-target .item-cell{ width:48px; height:48px; flex:none; cursor:default; transform:none; }
#ros-plan-ov .ros-farm-target .item-cell img{ width:32px; height:32px; }
#ros-plan-ov .ros-farm-target .card-cell{ width:44px; height:58px; }
#ros-plan-ov .ros-farm-target .card-cell img{ width:42px; height:56px; image-rendering:auto; }
#ros-plan-ov .ros-farm-target-meta{ flex:1; min-width:0; }
#ros-plan-ov .ros-farm-target-meta b{ display:block; font-size:13px; color:var(--ro-blue-3,#24418e); }
#ros-plan-ov .ros-farm-stage-note{ margin:6px 2px 4px; }
#ros-plan-ov .item-grid > .empty-note{ grid-column:1 / -1; margin:6px 2px; }
.ros-scroll{ overflow:auto; min-height:0; flex:1; display:flex; flex-direction:column; gap:10px; padding-right:2px; }
.ros-sec-title{ font-size:12px; font-weight:800; color:var(--ro-blue-3,#24418e); margin:2px 0 0; }
#ros-plan-ov .ros-deity-block{
  border:1px solid var(--ro-line,#d3dbef); border-radius:12px;
  padding:8px 8px 10px; display:flex; flex-direction:column; gap:8px;
}
#ros-plan-ov .ros-deity-block + .ros-deity-block{ margin-top:12px; }
#ros-plan-ov .ros-deity-skill{
  background:linear-gradient(180deg,#f6f2ff,#ebe4f8);
  border-color:#b7a7d9;
}
#ros-plan-ov .ros-deity-skill .ros-sec-title{ color:#5a3d9c; }
#ros-plan-ov .ros-deity-sub,
#ros-plan-ov .ros-sec-sub,
#ros-asp .ros-sec-sub{
  font-size:10px; font-weight:700;
}
#ros-plan-ov .ros-deity-sub{ color:#7a68a8; }
#ros-plan-ov .ros-sec-sub, #ros-asp .ros-sec-sub{ color:var(--ro-muted,#6c7896); }
#ros-asp .ro-title .ros-sec-sub{ color:inherit; opacity:.85; }
#ros-plan-ov .ros-deity-stat{
  background:linear-gradient(180deg,#f3f6ff,#e6edfb);
  border-color:var(--ro-blue-2,#3a5bb4);
}
#ros-plan-ov .ros-deity-note{
  font-size:11px; font-weight:700; line-height:1.45;
  color:#5a3d9c; text-align:center; padding:2px 6px 0;
}
.ros-skill-grid, .ros-item-grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(92px,1fr)); gap:6px; }
#ros-plan-ov .ros-item-grid .ros-chip{
  -webkit-user-select:none; user-select:none; -webkit-touch-callout:none;
}
#ros-plan-ov .ros-item-grid .ros-chip img,
#ros-plan-ov .ros-item-grid .ros-chip b,
#ros-plan-ov .ros-item-grid .ros-chip .ros-pri{
  pointer-events:none; -webkit-user-drag:none; user-select:none;
}
#ros-plan-ov .ros-item-grid .ros-chip .ros-x{ -webkit-user-drag:none; }
#ros-plan-ov .ros-item-grid.ros-sorting .ros-chip:hover{ transform:none; }
#ros-plan-ov .ros-chip.ros-lift{
  z-index:40; cursor:grabbing;
  box-shadow:0 12px 28px #24304f33, 0 0 0 2px #3a5bb466;
  border-color:var(--ro-blue-2,#3a5bb4);
  background:linear-gradient(160deg,#fff,#cfdef9);
  font-family:Nunito,"Noto Sans TC",sans-serif;
}
#ros-plan-ov .ros-chip.ros-lift b{
  font-family:Nunito,"Noto Sans TC",sans-serif;
  font-size:11px; font-weight:800; line-height:1.2;
}
#ros-plan-ov .ros-chip.ros-lift .ros-pri{
  font-family:Nunito,"Noto Sans TC",sans-serif;
  font-size:10px; font-weight:900; line-height:16px;
}
#ros-plan-ov .ros-chip.ros-slot-ph{ pointer-events:none; }
#ros-plan-ov .ros-perk-box{
  margin-top:2px; display:flex; flex-direction:column; gap:8px;
}
#ros-plan-ov .ros-perk-row-pair{
  display:flex; align-items:stretch; gap:10px;
}
#ros-plan-ov .ros-perk-open{
  flex:1; min-width:0; display:flex; align-items:center; gap:8px;
  padding:8px 10px; border-radius:12px; cursor:pointer; text-align:left;
  border:1px solid var(--ro-line,#d3dbef);
  background:linear-gradient(160deg,#fff,#e5edfb);
  color:var(--ro-text,#24304f); font:inherit;
}
#ros-plan-ov .ros-perk-open:hover{ border-color:var(--ro-blue-1,#6f8fd8); transform:translateY(-1px); }
#ros-plan-ov .ros-perk-open-text{ min-width:0; display:flex; align-items:baseline; flex-wrap:wrap; }
#ros-plan-ov .ros-perk-open .ros-sec-title{ margin:0; }
#ros-plan-ov .ros-perk-emoji, #ros-asp .ros-perk-emoji{
  flex:none; font-size:20px; line-height:1; width:28px; text-align:center;
}
#ros-plan-ov .ros-perk-row{
  display:flex; align-items:flex-start; gap:8px; margin:0;
}
#ros-plan-ov .ros-perk-copy, #ros-asp .ros-perk-copy{ flex:1; min-width:0; }
#ros-plan-ov .ros-perk-copy b, #ros-asp .ros-perk-copy b{ display:block; }
#ros-plan-ov .ros-perk-copy small, #ros-asp .ros-perk-copy small{
  display:block; margin-top:2px; color:var(--ro-muted,#6c7896);
  font-weight:600; line-height:1.35;
}
#ros-asp .ros-perk-section + .ros-perk-section{ margin-top:12px; }
#ros-asp .ros-perk-section{
  padding:8px; border-radius:12px; border:1px solid var(--ro-line,#d3dbef);
  background:linear-gradient(160deg,#f7f9ff,#e8eefb);
  display:flex; flex-direction:column; gap:8px;
}
#ros-asp .ros-perk-head{
  display:flex; align-items:center; gap:6px; margin-top:4px;
}
#ros-asp .ros-perk-head .ros-sec-title{ margin:0; }
#ros-asp .ros-perk-desc{
  color:var(--ro-muted,#6c7896); font-weight:600; line-height:1.35; margin:0 0 4px;
}
#ros-plan-ov .ros-loadout-head{
  display:flex; align-items:center; gap:12px;
}
#ros-plan-ov .ros-loadout-head-text{
  display:flex; flex-direction:column; gap:2px; min-width:0; flex:1;
}
#ros-plan-ov .ros-loadout-head .ros-sec-title{ margin:0; }
#ros-plan-ov .ros-loadout-head .ros-rotate{ flex:none; margin:0; }
.ros-chip{ position:relative; display:flex; flex-direction:column; align-items:center; gap:3px; padding:8px 4px 6px;
  border-radius:12px; cursor:pointer; border:1px solid var(--ro-line,#d3dbef);
  background:linear-gradient(160deg,#fff,#e5edfb); color:var(--ro-text,#24304f); font:inherit; }
.ros-chip:hover{ border-color:var(--ro-blue-1,#6f8fd8); transform:translateY(-1px); }
.ros-chip.on{ border-color:var(--ro-blue-2,#3a5bb4); box-shadow:0 0 0 2px #3a5bb44d; background:linear-gradient(160deg,#fff,#cfdef9); }
.ros-chip img{ width:28px; height:28px; image-rendering:pixelated; }
.ros-chip b{ font-size:11px; font-weight:800; color:var(--ro-blue-3,#24418e); text-align:center; line-height:1.2; }
.ros-chip .ros-pri{ position:absolute; left:5px; top:5px; font-size:10px; font-weight:900; color:#fff;
  background:var(--ro-blue-2,#3a5bb4); border-radius:8px; min-width:16px; padding:0 4px; line-height:16px; text-align:center; }
.ros-chip .ros-x{
  position:absolute; right:3px; top:3px; width:16px; height:16px; border:0; border-radius:8px;
  background:#ffffffd9; color:#24418e; font:800 11px/16px sans-serif; cursor:pointer; padding:0; }
.ros-job-open{ display:flex; align-items:center; gap:10px; width:100%; text-align:left;
  padding:8px 10px; border-radius:12px; cursor:pointer; border:1px solid var(--ro-line,#d3dbef);
  background:linear-gradient(160deg,#fff,#e5edfb); color:inherit; font:inherit; }
.ros-job-open:hover{ border-color:var(--ro-blue-1,#6f8fd8); }
.ros-job-open img{ width:40px; height:40px; image-rendering:pixelated; padding:4px;
  background:var(--ro-slot,#eef2fa); border:1px solid var(--ro-slot-border,#8b96b8); border-radius:10px; }
.ros-job-open b{ display:block; color:var(--ro-blue-3,#24418e); font-size:14px; }
.ros-job-open small{ color:var(--ro-muted,#6c7896); font-size:11px; font-weight:700; }
.wk-jobs{ display:grid; grid-template-columns:repeat(auto-fill,minmax(118px,1fr)); gap:6px; }
button.wk-job{ display:flex; flex-direction:column; align-items:center; gap:2px; padding:8px 4px; font:inherit; cursor:pointer;
  border-radius:12px; color:var(--ro-text,#24304f); border:1px solid var(--ro-line,#d3dbef);
  background:linear-gradient(160deg,#fff,#e5edfb); }
button.wk-job:hover{ border-color:var(--ro-blue-1,#6f8fd8); transform:translateY(-1px); }
button.wk-job.sel{ border-color:var(--ro-blue-2,#3a5bb4); box-shadow:0 0 0 2px #3a5bb44d; background:linear-gradient(160deg,#fff,#cfdef9); }
button.wk-job img{ width:28px; height:28px; image-rendering:pixelated; }
button.wk-job b{ font-size:11px; color:var(--ro-blue-3,#24418e); text-align:center; }
button.wk-job small{ font-size:10px; color:var(--ro-muted,#6c7896); text-align:center; }
.ros-rotate{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:12px; font-weight:700; color:var(--ro-text,#24304f); }
.ros-rotate input{ width:56px; padding:4px 6px; border:1px solid var(--ro-line,#d3dbef); border-radius:8px; font:inherit; font-weight:800; text-align:center; }
.ros-asp-row{ display:flex; align-items:center; gap:8px; padding:7px 8px; border:1px solid var(--ro-line,#d3dbef);
  border-radius:10px; background:#fff; }
.ros-asp-row.on{ border-color:var(--ro-blue-2,#3a5bb4); box-shadow:0 0 0 2px #3a5bb44d; }
.ros-asp-row b{ flex:1; font-size:13px; color:var(--ro-blue-3,#24418e); }
.ros-asp-row .ros-pri{ font-weight:900; color:var(--ro-blue-2,#3a5bb4); min-width:18px; }
.ros-asp-row button{ margin:0; padding:3px 8px; }
#ros-toast{ position:fixed; left:50%; bottom:134px; transform:translateX(-50%); z-index:80; pointer-events:none;
  padding:7px 12px; border-radius:10px; font:800 12px Nunito,"Noto Sans TC",sans-serif;
  background:linear-gradient(#fff,#f1f4fb); color:var(--ro-text,#24304f);
  border:1px solid var(--ro-border,#6b7ba8); box-shadow:0 6px 18px #00000059; opacity:0; transition:opacity .2s; }
#ros-toast.show{ opacity:1; }

`;

  let currentJob = null;
  let currentGender = store.gender || "m";
  let view = "plan"; // plan | jobs
  let jobLocked = false;
  let resetScreenManualPick = false;
  let uiTab = "build"; // build | farm
  let uiSub = { build: "skills", farm: "equip", perk: "skills" };
  let chestSlot = "potion";
  let perkChestSlot = "potion";
  let aspSkill = null;
  let perkPopKind = null;

  function el(tag, attrs, html) {
    const n = document.createElement(tag);
    if (attrs) for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") n.className = v;
      else if (k === "style" && v && typeof v === "object") Object.assign(n.style, v);
      else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2), v);
      else if (v === true) n.setAttribute(k, "");
      else if (v !== false && v != null) n.setAttribute(k, v);
    }
    if (html != null) n.innerHTML = html;
    return n;
  }

  function toast(msg) {
    let t = document.getElementById("ros-toast");
    if (!t) {
      t = el("div", { id: "ros-toast" });
      document.body.appendChild(t);
    }
    t.textContent = msg;
    placeToast();
    t.classList.add("show");
    clearTimeout(toast.tm);
    toast.tm = setTimeout(() => t.classList.remove("show"), 1600);
  }

  function channelInputGap(chat) {
    const form = (chat && (chat.querySelector("#chat-form") || chat.querySelector(".rc-form"))) || chat;
    const ch = form && form.querySelector(".chat-ch");
    const input = form && (form.querySelector("#chat-input") || form.querySelector("input"));
    if (ch && input) {
      const a = ch.getBoundingClientRect();
      const b = input.getBoundingClientRect();
      if (b.left > a.right - 0.5) return Math.max(0, b.left - a.right);
    }
    if (form) {
      const st = getComputedStyle(form);
      const n = parseFloat(st.columnGap || st.gap);
      if (Number.isFinite(n)) return n;
    }
    return 4;
  }

  function placeChat() {
    const btn = document.getElementById("ros-plan-btn");
    if (!btn) return;
    const hidden = btn.style.display === "none" || btn.classList.contains("hidden");
    if (hidden) return;
    const r = btn.getBoundingClientRect();
    for (const id of ["lobby-chat", "run-chat"]) {
      const chat = document.getElementById(id);
      if (!chat) continue;
      const gap = channelInputGap(chat);
      const ch = chat.querySelector(".chat-ch");
      const chatBox = chat.getBoundingClientRect();
      const inset = ch ? Math.max(0, ch.getBoundingClientRect().left - chatBox.left) : 0;
      const parent = chat.offsetParent || document.body;
      const pr = parent.getBoundingClientRect();
      const left = Math.max(0, r.right + gap - inset - pr.left);
      chat.style.setProperty("left", `${left}px`, "important");
    }
  }

  function placeToast() {
    const t = document.getElementById("ros-toast");
    if (!t) return;
    const skill = document.getElementById("skillbar");
    const items = document.getElementById("runitems");
    const vh = window.innerHeight;
    const gapFrom = (upper, lower) => {
      if (!upper || !lower) return 0;
      const u = upper.getBoundingClientRect();
      const l = lower.getBoundingClientRect();
      if (u.height <= 0 || l.height <= 0) return 0;
      return Math.max(0, l.top - u.bottom);
    };
    if (items && items.getBoundingClientRect().height > 0) {
      const ir = items.getBoundingClientRect();
      const gap = (skill && skill.getBoundingClientRect().height > 0)
        ? gapFrom(items, skill)
        : 14;
      t.style.bottom = `${Math.max(0, vh - ir.top + gap)}px`;
      return;
    }
    if (skill && skill.getBoundingClientRect().height > 0) {
      const sr = skill.getBoundingClientRect();
      const gap = 14;
      const itemsH = 34;
      t.style.bottom = `${Math.max(0, vh - sr.top + gap + itemsH + gap)}px`;
    }
  }

  function showTip(text, ev) {
    const tip = document.getElementById("ros-plan-tip");
    if (!tip) return;
    tip.textContent = text;
    tip.classList.remove("hidden");
    moveTip(ev);
  }
  function hideTip() {
    const tip = document.getElementById("ros-plan-tip");
    if (tip) tip.classList.add("hidden");
  }
  function moveTip(ev) {
    const tip = document.getElementById("ros-plan-tip");
    if (!tip || tip.classList.contains("hidden")) return;
    let x = ev.clientX + 16, y = ev.clientY + 12;
    const w = tip.offsetWidth || 80, h = tip.offsetHeight || 28;
    if (x + w > window.innerWidth - 8) x = ev.clientX - w - 12;
    if (y + h > window.innerHeight - 8) y = ev.clientY - h - 8;
    if (x < 8) x = 8;
    if (y < 8) y = 8;
    tip.style.left = `${x}px`;
    tip.style.top = `${y}px`;
  }

  function optSwitchControl(checked, onChange) {
    const lab = el("label", { class: "opt-check" });
    const inp = el("input", { type: "checkbox" });
    inp.checked = !!checked;
    inp.addEventListener("change", () => onChange(inp.checked, inp));
    lab.appendChild(inp);
    lab.appendChild(el("span", { class: "opt-switch" }));
    lab.addEventListener("click", (e) => e.stopPropagation());
    return lab;
  }

  function optSwitch(label, checked, onChange) {
    const row = el("div", { class: "opt-row" });
    row.appendChild(el("span", null, `<b>${label}</b>`));
    row.appendChild(optSwitchControl(checked, onChange));
    return row;
  }

  function renderFarmDiffDrop() {
    const box = el("div", { class: "ros-farm-diff" });
    const diff = el("div", { class: "diff" });
    const state = loadDifficulty();
    const loot = el("div", { class: "diff-reward" }, `${L("diffLoot")} <b data-out="drop">${diffLootText(state)}</b>`);
    const refreshLoot = () => {
      const b = loot.querySelector("[data-out=drop]");
      if (b) b.textContent = diffLootText(state);
    };
    for (const opt of DIFF_OPTS) {
      const lab = el("label", { class: "diff-row" });
      lab.appendChild(el("span", null, opt.names[lang] || opt.names.en));
      const inp = el("input", {
        type: "range",
        "data-key": opt.key,
        min: String(opt.min),
        max: String(opt.soloMax),
        step: "0.05",
        value: String(state[opt.key]),
      });
      const out = el("b", { "data-out": opt.key }, `${Math.round(state[opt.key] * 100)}%`);
      inp.addEventListener("input", () => {
        state[opt.key] = Number(inp.value);
        out.textContent = `${Math.round(state[opt.key] * 100)}%`;
        refreshLoot();
        saveDifficulty(state);
      });
      lab.appendChild(inp);
      lab.appendChild(out);
      diff.appendChild(lab);
    }
    diff.appendChild(loot);
    box.appendChild(diff);
    box.addEventListener("click", (e) => e.stopPropagation());
    return box;
  }

  function renderMoveDrop() {
    const box = el("div", { class: "ros-move-drop-inner" });
    const opts = moveOptsOf();
    box.appendChild(optSwitch(L("moveDodgeMob"), opts.dodgeMob !== false, (v) => {
      moveOptsOf().dodgeMob = v;
      saveStore();
    }));
    box.appendChild(optSwitch(L("moveDodgeBoss"), opts.dodgeBoss !== false, (v) => {
      moveOptsOf().dodgeBoss = v;
      saveStore();
    }));
    box.appendChild(optSwitch(L("movePickup"), opts.pickup !== false, (v) => {
      moveOptsOf().pickup = v;
      saveStore();
    }));
    box.addEventListener("click", (e) => e.stopPropagation());
    return box;
  }

  function renderMoveOption() {
    const row = el("div", { class: "opt-row ros-move-opt" + (moveDropOpen ? " ros-open" : "") });
    const head = el("div", { class: "ros-move-opt-head" });
    head.appendChild(el("span", null, `<b>${L("autoMove")}</b>`));
    head.appendChild(optSwitchControl(store.autoMove, (v) => {
      store.autoMove = v;
      if (!v) stopSteer(combatGame);
      saveStore();
      refreshBtn();
    }));
    head.addEventListener("click", (e) => {
      if (e.target && e.target.closest && e.target.closest(".opt-check")) return;
      e.stopPropagation();
      setMoveDropOpen(!moveDropOpen);
    });
    row.appendChild(head);
    const float = el("div", { class: "ros-move-drop-float" });
    float.appendChild(renderMoveDrop());
    float.addEventListener("pointerdown", (e) => e.stopPropagation());
    row.appendChild(float);
    return row;
  }

  function renderFarmOption() {
    const row = el("div", { class: "opt-row ros-farm-opt" + (farmDiffOpen ? " ros-open" : "") });
    const head = el("div", { class: "ros-farm-opt-head" });
    head.appendChild(el("span", null, `<b>${L("farm")}</b>`));
    head.appendChild(optSwitchControl(store.farm.enabled, (v, inp) => {
      if (v && !farmHasTargets()) {
        toast(L("farmNone"));
        if (inp) inp.checked = false;
        return;
      }
      store.farm.enabled = v;
      if (v) {
        resetFarmProgress();
        if (document.body.classList.contains("in-lobby")) {
          farmNextDone = false;
          farmNextUntil = 0;
          startFarmCountdown();
        }
      } else {
        hideFarmNext();
        farmNextDone = false;
        farmNextUntil = 0;
      }
      saveStore();
      refreshBtn();
    }));
    head.addEventListener("click", (e) => {
      if (e.target && e.target.closest && e.target.closest(".opt-check")) return;
      e.stopPropagation();
      setFarmDiffOpen(!farmDiffOpen);
    });
    row.appendChild(head);
    const float = el("div", { class: "ros-farm-diff-float" });
    float.appendChild(renderFarmDiffDrop());
    float.addEventListener("pointerdown", (e) => e.stopPropagation());
    row.appendChild(float);
    return row;
  }

  function renderWindow() {
    farmOwnedCache = null;
    const ov = document.getElementById("ros-plan-ov");
    if (!ov) return;
    const win = ov.querySelector(".ros-plan-window");
    if (!win) return;
    lang = gameLang();
    if (store.job && JOBS[store.job]) currentJob = store.job;
    else if (!currentJob || !JOBS[currentJob]) currentJob = null;
    if (store.gender === "f" || store.gender === "m") currentGender = store.gender;
    const title = view === "jobs" ? L("pickJob") : L("plan");
    win.innerHTML = "";
    const head = el("div", { class: "ro-title" });
    const label = el("span", { class: "ros-plan-label" });
    label.appendChild(document.createTextNode(title));
    if (view !== "jobs") {
      label.appendChild(document.createTextNode(" "));
      label.appendChild(el("span", { class: "ros-plan-ver" }, `(v${VERSION})`));
    }
    head.appendChild(label);
    if (view === "jobs") {
      const back = el("button", { class: "ro-btn ros-back", type: "button" }, L("back"));
      back.addEventListener("click", () => { view = "plan"; renderWindow(); });
      head.prepend(back);
    }
    const close = el("button", { class: "ro-x", type: "button", "aria-label": "close" }, "×");
    close.addEventListener("click", () => ov.classList.add("hidden"));
    head.appendChild(close);
    win.appendChild(head);
    const body = el("div", { class: "ro-body" });
    if (view === "jobs") body.appendChild(renderJobs());
    else body.appendChild(renderPlan());
    win.appendChild(body);
    if (view === "plan") {
      syncMoveDropFloat();
      if (uiTab === "farm") syncFarmDiffFloat();
    }
  }

  function renderJobs() {
    const wrap = el("div", { class: "ros-scroll" });
    const first = DATA.jobs.filter((j) => !SECOND.has(j.id));
    const second = DATA.jobs.filter((j) => SECOND.has(j.id));
    const block = (label, list) => {
      wrap.appendChild(el("div", { class: "ros-sec-title" }, label));
      const grid = el("div", { class: "wk-jobs" });
      for (const j of list) {
        const g = j.id === "bard" ? currentGender : "m";
        const btn = el("button", { class: "wk-job" + (j.id === currentJob ? " sel" : ""), type: "button" });
        btn.appendChild(el("img", { src: JOB_ICON(j.id, g), alt: "" }));
        btn.appendChild(el("b", null, jobName(j.id, g)));
        btn.appendChild(el("small", null, scalingLabel(j)));
        btn.addEventListener("click", () => {
          currentJob = j.id;
          store.job = j.id;
          jobLocked = true;
          manualJobOverride = true;
          if (isResetScreen()) resetScreenManualPick = true;
          if (j.id === "bard") store.gender = currentGender || "m";
          saveStore();
          view = "plan";
          renderWindow();
          refreshBtn();
        });
        grid.appendChild(btn);
      }
      wrap.appendChild(grid);
    };
    block(L("firstJobs"), first);
    block(L("secondJobs"), second);
    return wrap;
  }

  function renderSubTabs(items, current, onPick) {
    const tabs = el("div", { class: "ros-subtabs" });
    for (const [id, lab] of items) {
      const b = el("button", { class: "inv-chip" + (current === id ? " active" : ""), type: "button" }, lab);
      b.addEventListener("click", () => onPick(id));
      tabs.appendChild(b);
    }
    return tabs;
  }

  function renderPlan() {
    const wrap = el("div", { style: { display: "flex", flexDirection: "column", gap: "10px", minHeight: "0", flex: "1", overflow: "hidden" } });
    const hasJob = !!(currentJob && JOBS[currentJob]);
    const job = hasJob ? JOBS[currentJob] : null;
    const open = el("button", { class: "ros-job-open", type: "button" });
    open.appendChild(el("img", { src: hasJob ? JOB_ICON(currentJob, currentGender) : ICON("sa_advancedbook"), alt: "" }));
    const meta = el("span");
    meta.appendChild(el("b", null, hasJob ? jobName(currentJob, currentGender) : L("pickJob")));
    meta.appendChild(el("small", null, hasJob ? scalingLabel(job) : L("noJobHint")));
    open.appendChild(meta);
    open.addEventListener("click", () => { view = "jobs"; renderWindow(); });
    wrap.appendChild(open);

    const opts = el("div", { class: "ros-opts" });
    opts.appendChild(renderMoveOption());
    wrap.appendChild(opts);

    const tabs = el("div", { class: "ros-tabs" });
    for (const [id, lab] of [["build", L("build")], ["farm", L("farm")]]) {
      const b = el("button", { class: "tab-btn ro-btn" + (uiTab === id ? " primary" : ""), type: "button" }, lab);
      b.addEventListener("click", () => { uiTab = id; renderWindow(); });
      tabs.appendChild(b);
    }
    wrap.appendChild(tabs);

    const scroll = el("div", { class: "ros-scroll" });
    if (uiTab === "farm") {
      scroll.appendChild(renderFarmPanel());
    } else if (!hasJob) {
      const emptyBtn = el("button", { class: "ros-job-open", type: "button", style: { justifyContent: "center", textAlign: "center", padding: "18px 12px" } });
      emptyBtn.appendChild(el("small", null, L("pickJobFirst")));
      emptyBtn.addEventListener("click", () => { view = "jobs"; renderWindow(); });
      scroll.appendChild(emptyBtn);
    } else {
      scroll.appendChild(renderBuildPanel());
    }
    wrap.appendChild(scroll);
    return wrap;
  }


  const PERK_EMOJI = { reroll: "🔄", reroll_card: "🃏", banish: "🚫", focus: "🎯" };

  function perkEmojiEl(id) {
    return el("span", { class: "ros-perk-emoji" }, PERK_EMOJI[id] || "✨");
  }

  function titleWithSub(title, sub, titleClass) {
    const wrap = el("span", { class: titleClass || "ros-sec-title" });
    wrap.appendChild(document.createTextNode(title));
    if (sub) {
      wrap.appendChild(document.createTextNode(" "));
      wrap.appendChild(el("span", { class: "ros-sec-sub" }, sub));
    }
    return wrap;
  }

  function ensureAspOverlay() {
    let ov = document.getElementById("ros-asp");
    if (!ov) {
      ov = el("div", { id: "ros-asp", class: "ros-plan-overlay hidden" });
      const win = el("div", { class: "ro-window ros-asp-window" });
      ov.appendChild(win);
      ov.addEventListener("click", (e) => { if (e.target === ov) ov.classList.add("hidden"); });
      document.body.appendChild(ov);
    }
    return ov;
  }

  function focusTotalCount(plan) {
    const sk = (plan.perks && plan.perks.skills) || {};
    const ch = (plan.perks && plan.perks.chest) || {};
    let n = (Array.isArray(sk.focus) ? sk.focus.length : 0) + (Array.isArray(ch.focus) ? ch.focus.length : 0);
    if (sk.focusBasic) n += 1;
    return n;
  }

  function exileCount(perks, includeBasic) {
    const n = Array.isArray(perks.exile) ? perks.exile.length : 0;
    return n + (includeBasic && perks.exileBasic ? 1 : 0);
  }

  function togglePerkTarget(perks, kind, id, isBasic, scope) {
    // Always mutate the live plan object from planOf(). The `perks` argument may be a
    // stale reference after normalizePerks rebuilds plan.perks on the next planOf call.
    const plan = planOf(currentJob);
    const isChest = scope === "chest";
    const target = isChest ? plan.perks.chest : plan.perks.skills;
    const other = kind === "exile" ? "focus" : "exile";
    if (isBasic) {
      const next = !target[kind + "Basic"];
      if (next && kind === "exile") {
        if (exileCount(target, false) >= 2) {
          toast(L("exileMaxSkills"));
          return false;
        }
      }
      if (next && kind === "focus") {
        if (focusTotalCount(plan) >= 2 && !target.focusBasic) {
          toast(L("focusMax"));
          return false;
        }
      }
      target[kind + "Basic"] = next;
      if (next) target[other + "Basic"] = false;
      return true;
    }
    const arr = Array.isArray(target[kind]) ? target[kind].slice() : [];
    const on = arr.includes(id);
    if (on) {
      target[kind] = arr.filter((x) => x !== id);
      return true;
    }
    if (kind === "exile") {
      const used = exileCount(target, !isChest);
      if (used >= 2) {
        toast(isChest ? L("exileMaxItems") : L("exileMaxSkills"));
        return false;
      }
    }
    if (kind === "focus") {
      if (focusTotalCount(plan) >= 2) {
        toast(L("focusMax"));
        return false;
      }
    }
    arr.push(id);
    target[kind] = arr;
    target[other] = (Array.isArray(target[other]) ? target[other] : []).filter((x) => x !== id);
    return true;
  }

  function perkToggleChip(on, iconSrc, label, onClick) {
    const b = el("button", { class: "ros-chip" + (on ? " on" : ""), type: "button" });
    if (on) b.appendChild(el("span", { class: "ros-farm-mark" }, L("picked")));
    b.appendChild(el("img", { src: iconSrc, alt: "" }));
    b.appendChild(el("b", null, label));
    b.addEventListener("click", onClick);
    return b;
  }

  function renderPerkToggleRow(perks, key, icon, title, desc) {
    const row = el("div", { class: "opt-row ros-perk-row" });
    row.appendChild(perkEmojiEl(icon));
    const copy = el("div", { class: "ros-perk-copy" });
    copy.appendChild(el("b", null, title));
    copy.appendChild(el("small", null, desc));
    row.appendChild(copy);
    row.appendChild(optSwitchControl(perks[key] !== false, (v) => {
      perks[key] = !!v;
      saveStore();
    }));
    return row;
  }

  function renderPerkHead(kind) {
    const wrap = el("div");
    const head = el("div", { class: "ros-perk-head" });
    head.appendChild(perkEmojiEl(kind === "exile" ? "banish" : "focus"));
    head.appendChild(el("div", { class: "ros-sec-title" }, L(kind)));
    wrap.appendChild(head);
    wrap.appendChild(el("div", { class: "ros-perk-desc" }, L(kind === "exile" ? "perkExileDesc" : "perkFocusDesc")));
    return wrap;
  }

  function renderPerkSkillTargets(perks, kind) {
    const box = el("div");
    box.appendChild(renderPerkHead(kind));
    const { first, second } = jobSkills(currentJob);
    const addGrid = (ids, includeBasic) => {
      const grid = el("div", { class: "ros-skill-grid" });
      if (includeBasic) {
        const on = !!perks[kind + "Basic"];
        const b = perkToggleChip(on, basicAttackIcon(), L("basicAttack"), () => {
          togglePerkTarget(perks, kind, BASIC_SKILL_ID, true, "skills");
          saveStore();
          fillPerkPopup();
        });
        b.classList.add("ros-basic-chip");
        grid.appendChild(b);
      }
      for (const id of ids) {
        const sk = DATA.skills[id];
        if (!sk || isBasicSkillId(id)) continue;
        const on = (perks[kind] || []).includes(id);
        grid.appendChild(perkToggleChip(on, ICON(sk.icon), tName(sk.name) || sk.name, () => {
          togglePerkTarget(perks, kind, id, false, "skills");
          saveStore();
          fillPerkPopup();
        }));
      }
      box.appendChild(grid);
    };
    if (second.length) box.appendChild(el("div", { class: "ros-sec-title" }, L("firstJobs")));
    addGrid(first, true);
    if (second.length) {
      box.appendChild(el("div", { class: "ros-sec-title" }, L("secondJobs")));
      addGrid(second, false);
    }
    return box;
  }

  function renderPerkChestTargets(perks, kind) {
    const box = el("div");
    box.appendChild(renderPerkHead(kind));
    const slot = perkChestSlot || "potion";
    const grid = el("div", { class: "ros-item-grid" });
    const addItem = (id, iconSrc, label) => {
      const on = (perks[kind] || []).includes(id);
      grid.appendChild(perkToggleChip(on, iconSrc, label, () => {
        togglePerkTarget(perks, kind, id, false, "chest");
        saveStore();
        fillPerkPopup();
      }));
    };
    if (slot === "deity") {
      for (const id of jobSkillDeities(currentJob)) {
        const sk = DATA.skills[id];
        if (!sk) continue;
        addItem(id, ICON(sk.icon), tSkillDeity(id));
      }
    }
    for (const it of DATA.runItems.filter((x) => x.slot === slot)) {
      addItem(it.id, ITEM_ICON(it), tItem(it));
    }
    box.appendChild(grid);
    return box;
  }

  function perkChestSlotCount(kind, slotId) {
    const plan = planOf(currentJob);
    const perks = plan.perks.chest;
    const ids = Array.isArray(perks[kind]) ? perks[kind] : [];
    if (!ids.length) return 0;
    let n = 0;
    if (slotId === "deity") {
      const deities = new Set(jobSkillDeities(currentJob));
      for (const id of ids) if (deities.has(id)) n++;
      for (const it of DATA.runItems.filter((x) => x.slot === "deity")) {
        if (ids.includes(it.id)) n++;
      }
      return n;
    }
    const slotIds = new Set(DATA.runItems.filter((x) => x.slot === slotId).map((x) => x.id));
    for (const id of ids) if (slotIds.has(id)) n++;
    return n;
  }

  function renderPerkChestFilters(kind) {
    const filters = el("div", { class: "inv-filters" });
    for (const s of DATA.slots) {
      const count = perkChestSlotCount(kind, s.id);
      const lab = count > 0 ? `${tSlot(s.id)} (${count})` : tSlot(s.id);
      const b = el("button", { class: "inv-chip" + (perkChestSlot === s.id ? " active" : ""), type: "button" }, lab);
      b.addEventListener("click", () => { perkChestSlot = s.id; fillPerkPopup(); });
      filters.appendChild(b);
    }
    return filters;
  }

  function renderPerkRerollBody(which) {
    const plan = planOf(currentJob);
    const key = which === "rerollCard" ? "rerollCard" : "rerollAll";
    const icon = which === "rerollCard" ? "reroll_card" : "reroll";
    const desc = which === "rerollCard" ? L("perkRerollCardDesc") : L("perkRerollAllDesc");
    const wrap = el("div");
    const skillBox = el("div", { class: "ros-perk-section" });
    skillBox.appendChild(el("div", { class: "ros-sec-title" }, L("enhance")));
    skillBox.appendChild(renderPerkToggleRow(plan.perks.skills, key, icon, L(key === "rerollCard" ? "rerollCard" : "rerollAll"), desc));
    wrap.appendChild(skillBox);
    const chestBox = el("div", { class: "ros-perk-section" });
    chestBox.appendChild(el("div", { class: "ros-sec-title" }, L("chest")));
    chestBox.appendChild(renderPerkToggleRow(plan.perks.chest, key, icon, L(key === "rerollCard" ? "rerollCard" : "rerollAll"), desc));
    wrap.appendChild(chestBox);
    return wrap;
  }

  function renderPerkTargetBody(kind) {
    const plan = planOf(currentJob);
    const wrap = el("div");
    if (uiSub.perk !== "chest") uiSub.perk = "skills";
    wrap.appendChild(renderSubTabs(
      [["skills", L("enhance")], ["chest", L("chest")]],
      uiSub.perk,
      (id) => { uiSub.perk = id; fillPerkPopup(); }
    ));
    if (uiSub.perk === "chest") {
      const perks = plan.perks.chest;
      wrap.appendChild(renderPerkChestFilters(kind));
      wrap.appendChild(renderPerkChestTargets(perks, kind));
    } else {
      wrap.appendChild(renderPerkSkillTargets(plan.perks.skills, kind));
    }
    return wrap;
  }

  function fillPerkPopup() {
    if (!perkPopKind) return;
    const ov = ensureAspOverlay();
    const win = ov.querySelector(".ros-asp-window");
    if (!win) return;
    win.innerHTML = "";
    const reroll = perkPopKind === "rerollAll" || perkPopKind === "rerollCard";
    const title = el("div", { class: "ro-title" });
    title.appendChild(document.createTextNode(L(perkPopKind)));
    const close = el("button", { class: "ro-x", type: "button" }, "×");
    close.addEventListener("click", () => ov.classList.add("hidden"));
    title.appendChild(close);
    win.appendChild(title);
    const body = el("div", { class: "ro-body" });
    if (reroll) body.appendChild(renderPerkRerollBody(perkPopKind));
    else body.appendChild(renderPerkTargetBody(perkPopKind));
    win.appendChild(body);
    ov.classList.remove("hidden");
  }

  function openPerkPopup(kind) {
    aspSkill = null;
    perkPopKind = kind;
    fillPerkPopup();
  }

  function renderPerkOpenBtn(kind, icon, withSub) {
    const b = el("button", { class: "ros-perk-open", type: "button" });
    b.appendChild(perkEmojiEl(icon));
    const text = el("span", { class: "ros-perk-open-text" });
    text.appendChild(el("span", { class: "ros-sec-title" }, L(kind)));
    b.appendChild(text);
    b.addEventListener("click", () => openPerkPopup(kind));
    return b;
  }

  function renderPerkPanel() {
    const box = el("div", { class: "ros-perk-box" });
    const row1 = el("div", { class: "ros-perk-row-pair" });
    row1.appendChild(renderPerkOpenBtn("rerollAll", "reroll", true));
    row1.appendChild(renderPerkOpenBtn("rerollCard", "reroll_card", true));
    box.appendChild(row1);
    const row2 = el("div", { class: "ros-perk-row-pair" });
    row2.appendChild(renderPerkOpenBtn("exile", "banish", false));
    row2.appendChild(renderPerkOpenBtn("focus", "focus", false));
    box.appendChild(row2);
    return box;
  }

  function renderBuildPanel() {
    const box = el("div", { class: "ros-build-panel" });
    box.appendChild(optSwitch(L("autoPick"), store.auto, (v) => { store.auto = v; saveStore(); refreshBtn(); }));
    box.appendChild(renderPerkPanel());
    box.appendChild(renderSubTabs(
      [["skills", L("skills")], ["chest", L("chest")]],
      uiSub.build,
      (id) => { uiSub.build = id; renderWindow(); }
    ));
    box.appendChild(uiSub.build === "chest" ? renderChest() : renderSkills());
    return box;
  }

  function renderFarmPanel() {
    const box = el("div", { class: "ros-farm-panel" });
    box.appendChild(renderFarmOption());
    box.appendChild(optSwitch(L("farmMissingItems"), farmMissingOnly(), (v) => {
      store.farm.missingOnly = v;
      saveStore();
      renderWindow();
    }));
    box.appendChild(renderFarmStageRow());
    const stageNote = renderFarmStageNote();
    if (stageNote) box.appendChild(stageNote);
    box.appendChild(renderFarmTargetCard());
    const kind = uiSub.farm;
    const t = farmActiveTarget();
    if (t && t.kind === kind && (!farmSel || farmSel.kind !== kind)) farmSel = { kind, id: t.id };
    box.appendChild(renderSubTabs(
      [["equip", L("equip")], ["cards", L("cards")], ["pets", L("pets")]],
      kind,
      (id) => { uiSub.farm = id; renderWindow(); }
    ));
    box.appendChild(kind === "equip" ? renderEquipTab() : renderIdTab(kind));
    return box;
  }

  function renderSkills() {
    const box = el("div");
    const plan = planOf(currentJob);
    const { first, second } = jobSkills(currentJob);
    const max = maxSlots(currentJob);

    const head = el("div", { class: "ros-loadout-head" });
    const headText = el("div", { class: "ros-loadout-head-text" });
    headText.appendChild(el("div", { class: "ros-sec-title" }, `${L("loadout")} · ${plan.skills.length}/${max}`));
    headText.appendChild(el("div", { class: "ros-muted" }, L("loadoutHint")));
    head.appendChild(headText);
    const rot = el("div", { class: "ros-rotate" });
    rot.appendChild(document.createTextNode(L("rotate") + " "));
    const inp = el("input", { type: "number", min: "1", max: "99", value: String(loadoutRotateEvery(plan)) });
    inp.addEventListener("change", () => {
      const n = Math.max(1, Math.min(99, Math.round(Number(inp.value) || 5)));
      plan.rotateEvery = n;
      inp.value = String(n);
      saveStore();
    });
    rot.appendChild(inp);
    rot.appendChild(document.createTextNode(" " + L("rotateAfter")));
    head.appendChild(rot);
    box.appendChild(head);
    const load = el("div", { class: "ros-skill-grid" });
    {
      const basicOn = !!plan.basicOn;
      const b = el("button", { class: "ros-chip ros-basic-chip" + (basicOn ? " on" : ""), type: "button" });
      if (basicOn) b.appendChild(el("span", { class: "ros-pri" }, "B"));
      b.appendChild(el("img", { src: basicAttackIcon(), alt: "" }));
      b.appendChild(el("b", null, L("basicAttack")));
      b.addEventListener("click", () => openAspectPopup(BASIC_SKILL_ID));
      load.appendChild(b);
    }
    plan.skills.forEach((id, i) => {
      const s = DATA.skills[id];
      if (!s) return;
      const b = el("button", { class: "ros-chip on", type: "button" });
      b.appendChild(el("span", { class: "ros-pri" }, String(i + 1)));
      const x = el("button", { class: "ros-x", type: "button", title: L("remove") }, "×");
      x.addEventListener("click", (e) => {
        e.stopPropagation();
        plan.skills = plan.skills.filter((k) => k !== id);
        saveStore();
        renderWindow();
      });
      b.appendChild(x);
      b.appendChild(el("img", { src: ICON(s.icon), alt: "" }));
      b.appendChild(el("b", null, tName(s.name) || s.name));
      b.addEventListener("click", () => openAspectPopup(id));
      load.appendChild(b);
    });
    box.appendChild(load);

    const addPool = (label, ids, hint) => {
      if (!ids.length) return;
      box.appendChild(el("div", { class: "ros-sec-title" }, label));
      if (hint) box.appendChild(el("div", { class: "ros-muted", style: { margin: "2px 0 6px" } }, hint));
      const grid = el("div", { class: "ros-skill-grid" });
      for (const id of ids) {
        const s = DATA.skills[id];
        if (!s) continue;
        const on = plan.skills.includes(id);
        const b = el("button", { class: "ros-chip" + (on ? " on" : ""), type: "button" });
        if (on) b.appendChild(el("span", { class: "ros-pri" }, String(plan.skills.indexOf(id) + 1)));
        b.appendChild(el("img", { src: ICON(s.icon), alt: "" }));
        b.appendChild(el("b", null, tName(s.name) || s.name));
        b.addEventListener("click", () => {
          if (on) {
            plan.skills = plan.skills.filter((k) => k !== id);
            saveStore();
            renderWindow();
            return;
          }
          if (plan.skills.length >= max) return;
          plan.skills.push(id);
          skillAspectsOf(currentJob, id);
          saveStore();
          renderWindow();
        });
        grid.appendChild(b);
      }
      box.appendChild(grid);
    };
    addPool(second.length ? L("firstJobs") : L("pool"), first, L("poolHint"));
    if (second.length) addPool(L("secondJobs"), second);
    return box;
  }


  let chestDrag = null;
  function clearChestDrag() {
    if (!chestDrag) return;
    const d = chestDrag;
    chestDrag = null;
    if (d.timer) clearTimeout(d.timer);
    if (d.move) document.removeEventListener("pointermove", d.move);
    if (d.up) {
      document.removeEventListener("pointerup", d.up);
      document.removeEventListener("pointercancel", d.up);
    }
    if (d.ghost && d.ghost.parentNode) d.ghost.remove();
    if (d.chip) {
      d.chip.classList.remove("ros-slot-ph");
      d.chip.style.visibility = "";
    }
    if (d.grid) d.grid.classList.remove("ros-sorting");
  }
  function attachChestReorder(grid, plan) {
    const SLOP = 4;
    const isPicked = (n) => n && n.classList && n.classList.contains("ros-chip") && n.classList.contains("on");
    const refreshPri = () => {
      const picked = [...grid.querySelectorAll(".ros-chip.on")];
      picked.forEach((n, i) => {
        const p = n.querySelector(".ros-pri");
        if (p) p.textContent = String(i + 1);
      });
      if (chestDrag && chestDrag.ghost && chestDrag.chip) {
        const i = picked.indexOf(chestDrag.chip);
        const gp = chestDrag.ghost.querySelector(".ros-pri");
        if (gp && i >= 0) gp.textContent = String(i + 1);
      }
    };
    const commit = () => {
      const ids = [...grid.querySelectorAll(".ros-chip.on")].map((n) => n.getAttribute("data-chest-id")).filter(Boolean);
      const cur = plan.chest[chestSlot] || [];
      if (ids.length && ids.join("\0") !== cur.join("\0")) {
        plan.chest[chestSlot] = ids;
        saveStore();
      }
      refreshPri();
    };
    const movePlaceholder = (dest, placeholder) => {
      const firstUnpicked = [...grid.children].find((n) => n.classList.contains("ros-chip") && !n.classList.contains("on"));
      const slots = [...grid.children].filter(isPicked);
      const from = slots.indexOf(placeholder);
      if (from < 0 || dest === from || dest < 0 || dest >= slots.length) return;
      const firstRects = new Map(slots.map((n) => [n, n.getBoundingClientRect()]));
      const others = slots.filter((n) => n !== placeholder);
      others.splice(dest, 0, placeholder);
      others.forEach((n) => grid.insertBefore(n, firstUnpicked || null));
      others.forEach((n) => {
        if (n === placeholder) return;
        const first = firstRects.get(n);
        if (!first) return;
        if (n._rosFlipDone) n.removeEventListener("transitionend", n._rosFlipDone);
        n.style.transition = "none";
        n.style.transform = "";
        const last = n.getBoundingClientRect();
        const dx = first.left - last.left;
        const dy = first.top - last.top;
        if (!dx && !dy) {
          n.style.transition = "";
          return;
        }
        n.style.transform = "translate(" + dx + "px, " + dy + "px)";
        n.getBoundingClientRect();
        n.style.transition = "transform .22s cubic-bezier(.22,.75,.25,1)";
        n.style.transform = "";
        const done = (ev) => {
          if (ev && ev.propertyName && ev.propertyName !== "transform") return;
          n.style.transition = "";
          n.style.transform = "";
          n.removeEventListener("transitionend", done);
          if (n._rosFlipDone === done) n._rosFlipDone = null;
        };
        n._rosFlipDone = done;
        n.addEventListener("transitionend", done);
      });
      refreshPri();
    };
    const destFromPoint = (x, y, placeholder) => {
      const slots = [...grid.children].filter(isPicked);
      const from = slots.indexOf(placeholder);
      if (from < 0) return 0;
      const ph = placeholder.getBoundingClientRect();
      if (x >= ph.left && x <= ph.right && y >= ph.top && y <= ph.bottom) return from;
      const others = slots.filter((n) => n !== placeholder);
      if (!others.length) return from;
      const thresh = 0.25;
      const rects = others.map((n) => n.getBoundingClientRect());
      let bestI = 0, bestD = Infinity;
      for (let i = 0; i < rects.length; i++) {
        const r = rects[i];
        const cx = Math.max(r.left, Math.min(x, r.right));
        const cy = Math.max(r.top, Math.min(y, r.bottom));
        const rowPenalty = (y < r.top - 8 || y > r.bottom + 8) ? 1e5 : 0;
        const d = (x - cx) * (x - cx) + (y - cy) * (y - cy) + rowPenalty;
        if (d < bestD) { bestD = d; bestI = i; }
      }
      const r = rects[bestI];
      const slotIndex = bestI < from ? bestI : bestI + 1;
      const fromBefore = from < slotIndex;
      const sameRow = y >= r.top - 8 && y <= r.bottom + 8;
      if (sameRow) {
        if (fromBefore) return x >= r.left + r.width * thresh ? bestI + 1 : bestI;
        return x <= r.right - r.width * thresh ? bestI : bestI + 1;
      }
      if (fromBefore) return y >= r.top + r.height * thresh ? bestI + 1 : bestI;
      return y <= r.bottom - r.height * thresh ? bestI : bestI + 1;
    };
    grid.addEventListener("pointerdown", (e) => {
      if (e.button != null && e.button !== 0) return;
      const chip = e.target.closest(".ros-chip");
      if (!chip || !grid.contains(chip)) return;
      if (!chip.classList.contains("on")) return;
      let lastX = e.clientX;
      let lastY = e.clientY;
      clearChestDrag();
      const drag = { grid, chip, ghost: null, timer: null, move: null, up: null, started: false, ox: 0, oy: 0, dead: false };
      chestDrag = drag;
      const startLift = () => {
        if (drag.started || chestDrag !== drag) return;
        drag.started = true;
        grid._rosSkipClick = true;
        const r = chip.getBoundingClientRect();
        drag.ox = lastX - r.left;
        drag.oy = lastY - r.top;
        const ov = document.getElementById("ros-plan-ov") || document.body;
        const ghost = chip.cloneNode(true);
        ghost.classList.add("ros-lift");
        ghost.setAttribute("aria-hidden", "true");
        ghost.tabIndex = -1;
        ghost.style.position = "fixed";
        ghost.style.left = r.left + "px";
        ghost.style.top = r.top + "px";
        ghost.style.width = r.width + "px";
        ghost.style.height = r.height + "px";
        ghost.style.margin = "0";
        ghost.style.zIndex = "40";
        ghost.style.pointerEvents = "none";
        ghost.style.boxSizing = "border-box";
        ghost.style.transform = "none";
        const copyFont = (a, b) => {
          if (!a || !b) return;
          const cs = getComputedStyle(a);
          b.style.fontFamily = cs.fontFamily;
          b.style.fontSize = cs.fontSize;
          b.style.fontWeight = cs.fontWeight;
          b.style.fontStyle = cs.fontStyle;
          b.style.letterSpacing = cs.letterSpacing;
          b.style.lineHeight = cs.lineHeight;
          const ac = a.children, bc = b.children;
          for (let i = 0; i < ac.length && i < bc.length; i++) copyFont(ac[i], bc[i]);
        };
        copyFont(chip, ghost);
        ov.appendChild(ghost);
        drag.ghost = ghost;
        chip.classList.add("ros-slot-ph");
        chip.style.visibility = "hidden";
        grid.classList.add("ros-sorting");
        try { chip.setPointerCapture(e.pointerId); } catch (_) {}
      };
      const onMove = (ev) => {
        lastX = ev.clientX;
        lastY = ev.clientY;
        if (!drag.started) {
          if (Math.hypot(ev.clientX - e.clientX, ev.clientY - e.clientY) < SLOP) return;
          startLift();
          if (!drag.started) return;
        }
        ev.preventDefault();
        if (drag.ghost) {
          drag.ghost.style.left = (ev.clientX - drag.ox) + "px";
          drag.ghost.style.top = (ev.clientY - drag.oy) + "px";
        }
        movePlaceholder(destFromPoint(ev.clientX, ev.clientY, chip), chip);
      };
      const onUp = (ev) => {
        document.removeEventListener("pointermove", onMove);
        document.removeEventListener("pointerup", onUp);
        document.removeEventListener("pointercancel", onUp);
        drag.move = null;
        drag.up = null;
        if (!drag.started) {
          if (chestDrag === drag) chestDrag = null;
          return;
        }
        ev.preventDefault();
        const finish = () => {
          if (drag.dead) return;
          drag.dead = true;
          if (drag.ghost && drag.ghost.parentNode) drag.ghost.remove();
          drag.ghost = null;
          chip.classList.remove("ros-slot-ph");
          chip.style.visibility = "";
          grid.classList.remove("ros-sorting");
          commit();
          if (chestDrag === drag) chestDrag = null;
          setTimeout(() => { grid._rosSkipClick = false; }, 400);
        };
        if (drag.ghost) {
          const ph = chip.getBoundingClientRect();
          drag.ghost.style.transition = "left .18s cubic-bezier(.22,.75,.25,1), top .18s cubic-bezier(.22,.75,.25,1), transform .18s cubic-bezier(.22,.75,.25,1)";
          drag.ghost.style.left = ph.left + "px";
          drag.ghost.style.top = ph.top + "px";
          drag.ghost.style.transform = "scale(1)";
          drag.ghost.addEventListener("transitionend", finish, { once: true });
          setTimeout(finish, 260);
        } else finish();
      };
      grid.addEventListener("dragstart", (ev) => ev.preventDefault(), { once: true });
      drag.move = onMove;
      drag.up = onUp;
      document.addEventListener("pointermove", onMove, { passive: false });
      document.addEventListener("pointerup", onUp);
      document.addEventListener("pointercancel", onUp);
    });
  }
  function renderChestItemGrid(plan, slot) {
    const picked = plan.chest[slot] || [];
    const all = DATA.runItems.filter((it) => it.slot === slot);
    const grid = el("div", { class: "ros-item-grid" });
    const ordered = [...picked.map((id) => RUN[id]).filter(Boolean), ...all.filter((it) => !picked.includes(it.id))];
    for (const it of ordered) {
      const on = picked.includes(it.id);
      const b = el("button", { class: "ros-chip" + (on ? " on" : ""), type: "button", "data-chest-id": it.id });
      if (on) b.appendChild(el("span", { class: "ros-pri" }, String(picked.indexOf(it.id) + 1)));
      if (on) {
        const x = el("button", { class: "ros-x", type: "button", title: L("remove") }, "×");
        x.addEventListener("click", (e) => {
          e.stopPropagation();
          if (grid._rosSkipClick) return;
          plan.chest[slot] = picked.filter((k) => k !== it.id);
          saveStore();
          renderWindow();
        });
        b.appendChild(x);
      }
      b.appendChild(el("img", { src: ITEM_ICON(it), alt: "", draggable: "false" }));
      b.appendChild(el("b", null, tItem(it)));
      b.addEventListener("click", () => {
        if (grid._rosSkipClick) return;
        if (on) plan.chest[slot] = picked.filter((k) => k !== it.id);
        else plan.chest[slot] = picked.concat([it.id]);
        saveStore();
        renderWindow();
      });
      grid.appendChild(b);
    }
    attachChestReorder(grid, plan);
    return grid;
  }

  function renderSkillDeitySection(plan) {
    const ids = jobSkillDeities(currentJob);
    if (plan.skillDeity && !ids.includes(plan.skillDeity)) plan.skillDeity = null;
    const wrap = el("div", { class: "ros-deity-block ros-deity-skill" });
    const head = el("div", { class: "ros-sec-title ros-deity-skill-head" });
    head.appendChild(document.createTextNode(L("skillDeity")));
    head.appendChild(document.createTextNode(" "));
    head.appendChild(el("span", { class: "ros-deity-sub" }, L("skillDeitySub")));
    wrap.appendChild(head);
    const grid = el("div", { class: "ros-item-grid" });
    const ordered = plan.skillDeity && ids.includes(plan.skillDeity)
      ? [plan.skillDeity, ...ids.filter((id) => id !== plan.skillDeity)]
      : ids;
    for (const id of ordered) {
      const sk = DATA.skills[id];
      if (!sk) continue;
      const on = plan.skillDeity === id;
      const b = el("button", { class: "ros-chip" + (on ? " on" : ""), type: "button" });
      if (on) {
        b.appendChild(el("span", { class: "ros-farm-mark" }, L("picked")));
        const x = el("button", { class: "ros-x", type: "button", title: L("remove") }, "×");
        x.addEventListener("click", (e) => {
          e.stopPropagation();
          plan.skillDeity = null;
          saveStore();
          renderWindow();
        });
        b.appendChild(x);
      }
      b.appendChild(el("img", { src: ICON(sk.icon), alt: "", draggable: "false" }));
      b.appendChild(el("b", null, tSkillDeity(id)));
      b.addEventListener("click", () => {
        plan.skillDeity = on ? null : id;
        saveStore();
        renderWindow();
      });
      grid.appendChild(b);
    }
    wrap.appendChild(grid);
    if (plan.skillDeity) wrap.appendChild(el("div", { class: "ros-deity-note" }, L("skillDeityHint")));
    return wrap;
  }

  function renderChest() {
    clearChestDrag();
    const box = el("div");
    const plan = planOf(currentJob);
    const filters = el("div", { class: "inv-filters" });
    for (const s of DATA.slots) {
      let count = (plan.chest[s.id] || []).length;
      if (s.id === "deity" && plan.skillDeity) count += 1;
      const lab = count ? `${tSlot(s.id)} ${count}` : tSlot(s.id);
      const b = el("button", { class: "inv-chip" + (chestSlot === s.id ? " active" : ""), type: "button" }, lab);
      b.addEventListener("click", () => { chestSlot = s.id; renderWindow(); });
      filters.appendChild(b);
    }
    box.appendChild(filters);
    if (chestSlot === "deity") {
      box.appendChild(renderSkillDeitySection(plan));
      const stat = el("div", { class: "ros-deity-block ros-deity-stat" });
      stat.appendChild(el("div", { class: "ros-sec-title" }, L("statDeity")));
      stat.appendChild(renderChestItemGrid(plan, "deity"));
      box.appendChild(stat);
      return box;
    }
    box.appendChild(renderChestItemGrid(plan, chestSlot));
    return box;
  }

  function openAspectPopup(skillId) {
    perkPopKind = null;
    aspSkill = skillId;
    const sk = DATA.skills[skillId];
    let ov = document.getElementById("ros-asp");
    if (!ov) {
      ov = el("div", { id: "ros-asp", class: "ros-plan-overlay hidden" });
      const win = el("div", { class: "ro-window ros-asp-window" });
      ov.appendChild(win);
      ov.addEventListener("click", (e) => { if (e.target === ov) ov.classList.add("hidden"); });
      document.body.appendChild(ov);
    }
    const win = ov.querySelector(".ros-asp-window");
    const cfg = skillAspectsOf(currentJob, skillId);
    const typ = sk && DATA.types[sk.type];
    const avail = availableAspects(skillId);
    // ensure all type and skill-specific aspects exist in the list
    for (const a of avail) if (!cfg.aspects.includes(a)) cfg.aspects.push(a);
    cfg.aspects = cfg.aspects.filter((a) => avail.includes(a));

    win.innerHTML = "";
    const titleName = isBasicSkillId(skillId) ? L("basicAttack") : (tName(sk?.name) || skillId);
    const head = el("div", { class: "ro-title" }, `${titleName} · ${L("enhance")}`);
    const close = el("button", { class: "ro-x", type: "button" }, "×");
    close.addEventListener("click", () => ov.classList.add("hidden"));
    head.appendChild(close);
    win.appendChild(head);
    const body = el("div", { class: "ro-body" });
    if (isBasicSkillId(skillId)) {
      const plan = planOf(currentJob);
      body.appendChild(optSwitch(L("basicOn"), !!plan.basicOn, (v) => {
        plan.basicOn = !!v;
        saveStore();
        // refresh main window chip state if open
        const planOv = document.getElementById("ros-plan-ov");
        if (planOv && !planOv.classList.contains("hidden")) renderWindow();
      }));
      body.appendChild(el("div", { class: "ros-muted", style: { margin: "0 0 4px" } }, L("basicOnDesc")));

      const orderRow = el("div", { class: "opt-row ros-basic-order-row" });
      orderRow.appendChild(el("span", null, `<b>${L("basicOrderLabel")}</b>`));
      const btnGroup = el("div", { class: "ros-basic-order-btns" });
      const curOrder = normalizeBasicOrder(plan.basicOrder);
      const orderOpts = [
        ["2", "2"],
        ["3", "3"],
        ["4", "4"],
        ["last", L("basicOrderLast")],
      ];
      const orderBtns = [];
      for (const [val, lab] of orderOpts) {
        const b = el("button", { class: "inv-chip" + (curOrder === val ? " active" : ""), type: "button" }, lab);
        b.addEventListener("click", (e) => {
          e.stopPropagation();
          plan.basicOrder = val;
          saveStore();
          for (const ob of orderBtns) ob.btn.classList.toggle("active", ob.val === val);
        });
        orderBtns.push({ val, btn: b });
        btnGroup.appendChild(b);
      }
      orderRow.appendChild(btnGroup);
      body.appendChild(orderRow);
    }
    if (!avail.length) {
      body.appendChild(el("div", { class: "ros-sec-title" }, L("noAspect")));
    } else {
      const list = el("div", { style: { display: "flex", flexDirection: "column", gap: "6px", overflow: "auto" } });
      const redraw = () => {
        list.innerHTML = "";
        const en = enabledAspects(cfg);
        cfg.aspects.forEach((id, i) => {
          const on = !cfg.aspectOff.includes(id);
          const row = el("div", { class: "ros-asp-row" + (on ? " on" : "") });
          row.appendChild(el("span", { class: "ros-pri" }, on ? String(en.indexOf(id) + 1) : "–"));
          const nameBtn = el("button", { class: "ro-btn", type: "button", style: { flex: "1", margin: "0", textAlign: "left" } });
          nameBtn.appendChild(el("b", null, tAspect(id, skillId)));
          nameBtn.addEventListener("click", () => {
            if (on) cfg.aspectOff.push(id);
            else cfg.aspectOff = cfg.aspectOff.filter((x) => x !== id);
            saveStore();
            redraw();
          });
          row.appendChild(nameBtn);
          const up = el("button", { class: "ro-btn", type: "button" }, "▲");
          const down = el("button", { class: "ro-btn", type: "button" }, "▼");
          up.disabled = i === 0;
          down.disabled = i === cfg.aspects.length - 1;
          up.addEventListener("click", () => {
            if (i === 0) return;
            [cfg.aspects[i - 1], cfg.aspects[i]] = [cfg.aspects[i], cfg.aspects[i - 1]];
            saveStore();
            redraw();
          });
          down.addEventListener("click", () => {
            if (i >= cfg.aspects.length - 1) return;
            [cfg.aspects[i + 1], cfg.aspects[i]] = [cfg.aspects[i], cfg.aspects[i + 1]];
            saveStore();
            redraw();
          });
          row.appendChild(up);
          row.appendChild(down);
          list.appendChild(row);
        });
      };
      redraw();
      body.appendChild(list);
    }
    win.appendChild(body);
    ov.classList.remove("hidden");
  }

  function refreshBtn() {
    lang = gameLang();
    const btn = document.getElementById("ros-plan-btn");
    if (!btn) return;
    syncJobFromLobby();
    const img = btn.querySelector("img");
    if (img && img.getAttribute("src") !== ICON("sa_advancedbook")) img.src = ICON("sa_advancedbook");
    const dot = btn.querySelector(".ros-dot");
    if (dot) dot.classList.toggle("off", !(store.auto || store.autoMove));
    if (btn.style.display === "none") btn.style.display = "flex";
    btn.classList.remove("hidden");
    placeChat();
  }

  /* -------------------- party / tower gate -------------------- */
  function objHasParty(o, isCombat) {
    if (!o || typeof o !== "object") return false;
    if (o.party === true || o.isParty === true || o.inParty === true || o.multiplayer === true || o.coOp === true || o.coop === true) return true;
    if (typeof o.partyId === "string" && o.partyId.trim().length > 0) return true;
    if (typeof o.partyId === "number" && o.partyId > 0) return true;
    if (typeof o.partySize === "number" && o.partySize > 1) return true;
    if (o.party && typeof o.party === "object") {
      if (Array.isArray(o.party.members) && o.party.members.filter(Boolean).length > 1) return true;
      if (Array.isArray(o.party.players) && o.party.players.filter(Boolean).length > 1) return true;
      if (o.party.id || o.party.partyId || o.party.code) return true;
    }
    if (o.room && typeof o.room === "object") {
      if (Array.isArray(o.room.members) && o.room.members.filter(Boolean).length > 1) return true;
      if (Array.isArray(o.room.players) && o.room.players.filter(Boolean).length > 1) return true;
    }
    if (Array.isArray(o.players) && o.players.filter(Boolean).length > 1) return true;
    if (Array.isArray(o.mates) && o.mates.filter(Boolean).length > 0) return true;
    if (Array.isArray(o.teammates) && o.teammates.filter(Boolean).length > 0) return true;
    if (isCombat && Array.isArray(o.others) && o.others.filter(Boolean).length > 0) return true;
    if (Array.isArray(o.others) && o.others.some((x) => x && (x.teammate || x.party || x.isPartyMember || x.inParty))) return true;
    if (o.partyMembers) {
      if (Array.isArray(o.partyMembers) && o.partyMembers.filter(Boolean).length > 1) return true;
      if (typeof o.partyMembers === "object" && !Array.isArray(o.partyMembers) && Object.keys(o.partyMembers).length > 1) return true;
    }
    return false;
  }

  function isInParty() {
    try {
      if (objHasParty(combatGame, true)) return true;
      const pl = (typeof lobbyPlaza === "function" ? lobbyPlaza() : null) || livePlaza || lobbyGame;
      if (objHasParty(pl, false)) return true;
      for (const o of pendingGames) {
        if (objHasParty(o, isCombatGame(o))) return true;
      }

      const acc = gameStoreGet("ro-survivors.account.v1") || {};
      if (acc.partyId || acc.inParty === true) return true;

      const partyContainers = document.querySelectorAll("#party, #party-hud, #party-panel, #party-list, #party-box, .party-hud, .party-panel, .party-list, .party-box, [id*='party']");
      for (const box of partyContainers) {
        if (!box || box.id.startsWith("ros-")) continue;
        if (box.classList.contains("hidden") || box.offsetParent === null) continue;
        const members = box.querySelectorAll("[data-member], [data-uid], [data-pid], .party-member, .pt-member, .party-row, .member");
        if (members.length > 1) return true;
        const txt = (box.textContent || "");
        if (/離開隊伍|解散隊伍|退出隊伍|Leave party|Disband party|Salir del grupo|Sair do grupo/i.test(txt)) return true;
      }
      if (document.querySelector("#lobby-labels .lobby-name.party, #lobby-labels .lobby-name.mate, #lobby-labels .lobby-name.teammate")) return true;
      if (document.body.classList.contains("in-party") || document.body.classList.contains("coop") || document.body.classList.contains("multiplayer")) return true;
    } catch (_) {}
    return false;
  }

  function isInMonsterTower() {
    try {
      const g = combatGame;
      if (g) {
        if (g.isTower === true || g.tower === true || g.mode === "tower" || g.gameMode === "tower") return true;
        if (typeof g.towerFloor === "number" && g.towerFloor > 0) return true;
        const sid = String(g.stageId || g.stage || g.mapId || g.map || "").toLowerCase();
        if (/tower|魔塔|終結塔|monster.?tower|md_tower/.test(sid)) return true;
        const name = String(g.stageName || g.mapName || "").toLowerCase();
        if (/tower|魔物終結|monster.?tower|torre/.test(name)) return true;
      }
      for (const elId of ["stage-name", "hud-stage", "tower-floor", "hud-floor"]) {
        const el = document.getElementById(elId);
        if (!el || el.classList.contains("hidden")) continue;
        const txt = (el.textContent || "").trim();
        if (/魔物終結塔|Monster Tower|Torre/i.test(txt)) return true;
      }
      const loadEl = document.getElementById("loading");
      if (loadEl && !loadEl.classList.contains("hidden")) {
        const ltxt = (loadEl.textContent || "").trim();
        if (/魔物終結塔|Monster Tower|Torre/i.test(ltxt)) return true;
      }
      if (document.body.classList.contains("tower") || document.body.classList.contains("monster-tower") || document.body.classList.contains("in-tower")) return true;
    } catch (_) {}
    return false;
  }

  function featuresBlocked() {
    return isInParty() || isInMonsterTower();
  }

  function applyPartyTowerGate() {
    const blocked = featuresBlocked();
    const btn = document.getElementById("ros-plan-btn");
    if (blocked) {
      let changed = false;
      if (store.auto) { store.auto = false; changed = true; }
      if (store.autoMove) { store.autoMove = false; changed = true; }
      if (store.farm && store.farm.enabled) { store.farm.enabled = false; changed = true; }
      hideFarmNext();
      farmNextDone = false;
      farmNextUntil = 0;
      farmStopKeyWalk();
      stopSteer(combatGame);
      if (changed) {
        saveStore();
        refreshBtn();
      }
      const planOv = document.getElementById("ros-plan-ov");
      if (planOv && !planOv.classList.contains("hidden")) planOv.classList.add("hidden");
      const asp = document.getElementById("ros-asp");
      if (asp && !asp.classList.contains("hidden")) asp.classList.add("hidden");
      if (btn) {
        btn.style.cursor = "not-allowed";
        btn.classList.add("ros-blocked");
      }
    } else {
      if (btn) {
        btn.style.cursor = "";
        btn.classList.remove("ros-blocked");
      }
    }
    for (const inp of document.querySelectorAll("#ros-plan-ov .opt-check input")) {
      if (blocked) {
        inp.disabled = true;
        const row = inp.closest(".opt-row, .ros-farm-opt");
        if (row) row.style.cursor = "not-allowed";
      } else {
        inp.disabled = false;
        const row = inp.closest(".opt-row, .ros-farm-opt");
        if (row) row.style.cursor = "";
      }
    }
  }

  function hidePlanGate() {
    const el = document.getElementById("ros-plan-gate");
    if (el) {
      el.classList.add("hidden");
      el.classList.remove("overlay");
    }
  }
  function ensurePlanGateUi() {
    let el = document.getElementById("ros-plan-gate");
    if (el) return el;
    el = document.createElement("div");
    el.id = "ros-plan-gate";
    el.className = "overlay hidden";
    el.innerHTML = '<div class="ro-window small-window"><div class="ro-title"></div><div class="ro-body center"><div class="npc-text" id="ros-plan-gate-text"></div></div><div class="btn-row pad"><button type="button" class="ro-btn" id="ros-plan-gate-ok"></button></div></div>';
    document.body.appendChild(el);
    el.querySelector("#ros-plan-gate-ok").addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      hidePlanGate();
    });
    return el;
  }
  function showPlanGate(msgKey, titleKey) {
    lang = gameLang();
    const el = ensurePlanGateUi();
    const title = el.querySelector(".ro-title");
    const text = document.getElementById("ros-plan-gate-text");
    const btn = document.getElementById("ros-plan-gate-ok");
    if (title) title.textContent = L(titleKey || "noticeTitle");
    if (text) {
      const msg = L(msgKey || "planNeedJobLv");
      text.style.whiteSpace = "pre-line";
      text.style.textAlign = "center";
      text.textContent = msg;
    }
    if (btn) btn.textContent = L("confirm");
    el.classList.add("overlay");
    el.classList.remove("hidden");
  }

  function ensureUI() {
    if (document.getElementById("ros-plan-style")) return;
    const st = el("style", { id: "ros-plan-style" });
    st.textContent = css;
    document.documentElement.appendChild(st);

    const btn = el("button", { id: "ros-plan-btn", type: "button" });
    btn.appendChild(el("img", { src: ICON("sa_advancedbook"), alt: "" }));
    const dot = el("span", { class: "ros-dot" + (store.auto || store.autoMove ? "" : " off") });
    btn.appendChild(dot);
    btn.addEventListener("click", () => {
      hideTip();
      applyPartyTowerGate();
      if (featuresBlocked()) {
        const planOv = document.getElementById("ros-plan-ov");
        if (planOv) planOv.classList.add("hidden");
        const asp = document.getElementById("ros-asp");
        if (asp) asp.classList.add("hidden");
        showPlanGate("partyTowerBlocked", "noticeTitle");
        return;
      }
      if (!planUnlocked()) {
        const planOv = document.getElementById("ros-plan-ov");
        if (planOv) planOv.classList.add("hidden");
        const asp = document.getElementById("ros-asp");
        if (asp) asp.classList.add("hidden");
        showPlanGate("planNeedJobLv", "plan");
        return;
      }
      hidePlanGate();
      const ov = document.getElementById("ros-plan-ov");
      syncJobFromLobby();
      view = "plan";
      ov.classList.toggle("hidden");
      if (!ov.classList.contains("hidden")) renderWindow();
    });
    btn.addEventListener("pointerenter", (e) => showTip(L("plan"), e));
    btn.addEventListener("pointermove", moveTip);
    btn.addEventListener("pointerleave", hideTip);
    document.body.appendChild(btn);

    const tip = el("div", { id: "ros-plan-tip", class: "tooltip hidden" });
    document.body.appendChild(tip);

    const ov = el("div", { id: "ros-plan-ov", class: "ros-plan-overlay hidden" });
    const win = el("div", { class: "ro-window ros-plan-window" });
    ov.appendChild(win);
    ov.addEventListener("click", (e) => { if (e.target === ov) ov.classList.add("hidden"); });
    document.body.appendChild(ov);

    placeChat();
    window.addEventListener("resize", () => { placeChat(); placeToast(); });
  }

  function watch() {
    const ready = () => {
      const picker = document.getElementById("picker");
      if (picker && !picker.__rosWatched) {
        picker.__rosWatched = true;
        new MutationObserver(() => tryAutoPick()).observe(picker, {
          childList: true, subtree: true, attributes: true, attributeFilter: ["class"],
        });
      }
      const onHud = () => {
        clearTimeout(onHud.t);
        onHud.t = setTimeout(refreshBtn, 80);
      };
      const hudName = document.getElementById("hud-name");
      if (hudName && !hudName.__rosWatched) {
        hudName.__rosWatched = true;
        new MutationObserver(onHud).observe(hudName, { childList: true, characterData: true, subtree: true });
      }
      const hud = document.getElementById("hud");
      if (hud && !hud.__rosWatched) {
        hud.__rosWatched = true;
        new MutationObserver(onHud).observe(hud, { attributes: true, attributeFilter: ["class"] });
      }
      if (document.body && !document.body.__rosWatched) {
        document.body.__rosWatched = true;
        new MutationObserver(() => {
          try { syncJobFromLobby(); refreshBtn(); } catch (_) {}
        }).observe(document.body, { attributes: true, attributeFilter: ["class"] });
      }
      for (const ovId of ["charselect", "splash", "charcreate"]) {
        const elOv = document.getElementById(ovId);
        if (elOv && !elOv.__rosWatched) {
          elOv.__rosWatched = true;
          new MutationObserver(() => {
            try { syncJobFromLobby(); refreshBtn(); } catch (_) {}
          }).observe(elOv, { attributes: true, attributeFilter: ["class", "style"] });
        }
      }
    };
    ready();
    // lobby / hud may appear later — observe documentElement childList only (not subtree) to avoid load loops
    const boot = new MutationObserver(() => {
      if (document.getElementById("picker") || document.getElementById("hud") || document.getElementById("lobby-chat")) {
        ensureUI();
        ready();
        placeChat();
      }
    });
    boot.observe(document.documentElement, { childList: true, subtree: false });
    window.addEventListener("storage", (e) => {
      if (e.key === "ro-survivors:settings") applyGameLang(true);
      if (e.key === "ro-survivors.characters.v1" || e.key === "ro-survivors:settings") refreshBtn();
    });
    document.addEventListener("pointerdown", (e) => {
      if (farmPointer) return;
      const t = e.target;
      if (t && t.closest && t.closest("#charselect")) {
        try { noteCharSelectNode(t); } catch (_) {}
      }
      if (t && (t.closest && (t.closest("#stage") || t.closest("canvas")) || t.tagName === "CANVAS")) {
        lastUserPointer = performance.now();
      }
    }, true);
    if (!watch.__farm) watch.__farm = setInterval(farmTick, 400);
    if (!watch.__pick) watch.__pick = setInterval(() => { ready(); tryAutoPick(true); }, 350);
    if (!watch.__gate) watch.__gate = setInterval(() => { try { applyPartyTowerGate(); syncJobFromLobby(); } catch (_) {} }, 500);
    if (!watch.__save) {
      watch.__save = true;
      const raw = localStorage.setItem.bind(localStorage);
      localStorage.setItem = function (k, v) {
        raw(k, v);
        if (k === "ro-survivors:settings") {
          clearTimeout(applyGameLang.t);
          applyGameLang.t = setTimeout(() => applyGameLang(true), 50);
        }
        if (k === "ro-survivors.characters.v1" || k === "ro-survivors.account.v1" || k === "ro-survivors.pets.v1" || k === "ro-survivors-session" || k === "ro-survivors-guest-session") {
          if (isResetScreen()) resetJobSelection();
          try { syncJobFromLobby(); refreshBtn(); } catch (_) {}
          farmOwnedCache = null;
          clearTimeout(syncBasicAttackIcon.t);
          syncBasicAttackIcon.t = setTimeout(() => {
            syncBasicAttackIcon();
            const ov = document.getElementById("ros-plan-ov");
            if (ov && !ov.classList.contains("hidden") && uiTab === "farm") renderWindow();
          }, 50);
        }
      };
    }
  }


  (function antiHiddenPause() {
    let lastResume = 0;
    const tick = () => {
      try {
        if (document.hidden && combatGame && combatGame.state === "paused") {
          const settings = JSON.parse(localStorage.getItem("ro-survivors:settings") || "{}");
          const autoPause = settings && (settings.autoPause !== false && settings.pauseOnBlur !== false && settings.pauseHidden !== false);
          // If game still pauses while settings say off, force resume when maximized other window covers
          if (settings && (settings.autoPause === false || settings.pauseOnBlur === false || settings.pauseWhenHidden === false || settings.pauseOnHide === false)) {
            if (performance.now() - lastResume > 500) {
              lastResume = performance.now();
              if (typeof combatGame.resume === "function") combatGame.resume();
              else if (typeof combatGame.unpause === "function") combatGame.unpause();
              else combatGame.state = "playing";
            }
          }
        }
      } catch (_) {}
    };
    document.addEventListener("visibilitychange", tick);
    setInterval(tick, 800);
  })();

  (function patchScrollIntoView() {
    const orig = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function () {
      try {
        const inChar = this.closest && (this.closest("#inventory") || this.closest(".inv-box") || this.closest("#equip") || this.closest(".card-slot"));
        if (inChar) {
          // keep current scroll position of nearest scroll parent
          return;
        }
      } catch (_) {}
      return orig.apply(this, arguments);
    };
  })();
  function start() {
    installGameHook();
    if (document.body) ensureUI();
    const det = detectJob();
    currentJob = null;
    jobLocked = false;
    manualJobOverride = false;
    resetScreenManualPick = false;
    try { syncJobFromLobby(); } catch (_) {}
    try { applyPartyTowerGate(); } catch (_) {}
    refreshBtn();
    watch();
  }

  
  // Expose inspection and experimental parameters for Playwright & Console
  try {
    window.__ROS_CUSTOM_BOT__ = {
      version: VERSION,
      isUnlocked: () => planUnlocked(),
      getStore: () => store,
      getCombatGame: () => combatGame,
      isCombatActive: () => isCombatActive(),
      setGodMode: (enabled, threshold) => {
        experimentalGodMode = !!enabled;
        if (typeof threshold === "number" && threshold > 0) {
          godModeHpThreshold = threshold;
        }
        if (combatGame) combatGame.god = false;
        saveCheatSettings();
        updateVisualStatusBadge();
        console.log("[ROS] 擬真保護模式 set to:", experimentalGodMode, "門檻:", godModeHpThreshold + "%");
      },
      setHpThreshold: (threshold) => {
        if (typeof threshold === "number" && threshold > 0) {
          godModeHpThreshold = threshold;
          saveCheatSettings();
          updateVisualStatusBadge();
          console.log("[ROS] 擬真保護門檻 set to:", godModeHpThreshold + "%");
        }
      },
      setDamageMultiplier: (mult) => {
        experimentalDamageMult = Math.max(1, Number(mult) || 1);
        saveCheatSettings();
        updateVisualStatusBadge();
        console.log("[ROS] Damage multiplier set to:", experimentalDamageMult);
      },
      getCheatsStatus: () => ({ godMode: experimentalGodMode, hpThreshold: godModeHpThreshold, damageMult: experimentalDamageMult }),
      updateBadge: () => updateVisualStatusBadge()
    };
    if (document.body) updateVisualStatusBadge();
    else document.addEventListener("DOMContentLoaded", updateVisualStatusBadge);
  } catch (_) {}

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();