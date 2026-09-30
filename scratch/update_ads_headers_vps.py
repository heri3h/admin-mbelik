import os
import glob
import subprocess

ADS_HEADER_TEMPLATE = """<?php
// Auto-Pricing GAM Header Script - Zero-Fallback Architecture (0ms Latency, Instant GEO & Smart Tiered Cascade)
$phpAdUnits = array();
$phpFallbackBnr = "f10000";
$phpFallbackInt = "f35000";
$phpFallbackAnc = "f15000";

$detectedCountry = strtoupper($_SERVER['HTTP_CF_IPCOUNTRY'] ?? $_SERVER['HTTP_X_COUNTRY'] ?? $_SERVER['GEOIP_COUNTRY_CODE'] ?? 'ID');

$defaultHeader = "/22806125615/play-1";
$defaultFeed   = "/22806125615/play-2";
$defaultSide   = "/22806125615/play-3";
$defaultSide2  = "/22806125615/play-4";
$defaultInt    = "/22806125615/play-5";
$defaultSticky = "/22806125615/play-6";

$dirPath = __DIR__;
$pricingConfigFile = $dirPath . '/../../pricing_config.json';
if (!file_exists($pricingConfigFile)) $pricingConfigFile = $dirPath . '/../pricing_config.json';
if (!file_exists($pricingConfigFile)) $pricingConfigFile = $dirPath . '/pricing_config.json';

$cfgJson = null;
if (file_exists($pricingConfigFile)) {
    $cfgContent = @file_get_contents($pricingConfigFile);
    if ($cfgContent) {
        $cfgJson = @json_decode($cfgContent, true);
        if (is_array($cfgJson) && isset($cfgJson['ad_units'])) {
            $phpAdUnits = $cfgJson['ad_units'];
        }
    }
}

$currentPricingFile = $dirPath . '/../../current_pricing.json';
if (!file_exists($currentPricingFile)) $currentPricingFile = $dirPath . '/../current_pricing.json';
if (!file_exists($currentPricingFile)) $currentPricingFile = $dirPath . '/current_pricing.json';

$cpJson = null;
if (file_exists($currentPricingFile)) {
    $cpContent = @file_get_contents($currentPricingFile);
    if ($cpContent) {
        $cpJson = @json_decode($cpContent, true);
        if (is_array($cpJson) && isset($cpJson['summary'])) {
            $s = $cpJson['summary'];
            if (isset($s['bnr']['ecpm']) && floatval($s['bnr']['ecpm']) > 0) {
                $e = floatval($s['bnr']['ecpm']);
                if ($e >= 30000) $phpFallbackBnr = "f30000";
                else if ($e >= 25000) $phpFallbackBnr = "f25000";
                else if ($e >= 20000) $phpFallbackBnr = "f20000";
                else if ($e >= 15000) $phpFallbackBnr = "f15000";
                else if ($e >= 10000) $phpFallbackBnr = "f10000";
            }
            if (isset($s['int']['ecpm']) && floatval($s['int']['ecpm']) > 0) {
                $e = floatval($s['int']['ecpm']);
                if ($e >= 35000) $phpFallbackInt = "f35000";
                else if ($e >= 30000) $phpFallbackInt = "f30000";
                else if ($e >= 25000) $phpFallbackInt = "f25000";
                else if ($e >= 20000) $phpFallbackInt = "f20000";
                else if ($e >= 15000) $phpFallbackInt = "f15000";
            }
            if (isset($s['anc']['ecpm']) && floatval($s['anc']['ecpm']) > 0) {
                $e = floatval($s['anc']['ecpm']);
                if ($e >= 30000) $phpFallbackAnc = "f30000";
                else if ($e >= 25000) $phpFallbackAnc = "f25000";
                else if ($e >= 20000) $phpFallbackAnc = "f20000";
                else if ($e >= 15000) $phpFallbackAnc = "f15000";
            }
        }
    }
}
?>
<!-- Global site tag (gtag.js) - Google Ads -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-16785269892/nNVJCMe5mowaEITJ68M-"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'AW-16785269892/nNVJCMe5mowaEITJ68M-');
</script>

<script>
window.MBELIK_COUNTRY = <?php echo json_encode($detectedCountry); ?>;
window.MBELIK_INLINE_CURRENT_PRICING = <?php echo json_encode($cpJson); ?>;
window.MBELIK_INLINE_PRICING_CONFIG = <?php echo json_encode($cfgJson); ?>;
</script>

<script async src="https://securepubads.g.doubleclick.net/tag/js/gpt.js"></script>
<script>
window.googletag = window.googletag || { cmd: [] };

var phpFallbackBnr = <?php echo json_encode($phpFallbackBnr); ?>;
var phpFallbackInt = <?php echo json_encode($phpFallbackInt); ?>;
var phpFallbackAnc = <?php echo json_encode($phpFallbackAnc); ?>;

var mbelikPricingVal = phpFallbackBnr;
var slotHeader, slotFeed, slotSide1, slotSide2, slotInt, slotSticky;
window.slotStateMap = window.slotStateMap || {};
window.pricingEngineResolved = false;

function detectDevice() {
    var ua = navigator.userAgent || navigator.vendor || window.opera;
    if (/android/i.test(ua)) return 'mobile';
    if (/iPhone|iPod/i.test(ua)) return 'mobile';
    if (/iPad/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)) return 'mobile';
    return 'desktop';
}

function fetchWithTimeout(url, options, timeoutMs) {
    return new Promise(function(resolve, reject) {
        var timer = setTimeout(function() {
            reject(new Error("Request timeout"));
        }, timeoutMs);

        fetch(url, options).then(
            function(response) {
                clearTimeout(timer);
                resolve(response);
            },
            function(err) {
                clearTimeout(timer);
                reject(err);
            }
        );
    });
}

function findRuleWithStepDown(targetCPM, matchRate, targetMr, rules, emergencyMr, fmtName, fmtThreshold) {
    var emergencyThreshold = (typeof emergencyMr === 'number') ? emergencyMr : 15.0;
    var hardFloorMin = (typeof fmtThreshold === 'number') ? fmtThreshold : 65.0;

    if (matchRate > 0 && matchRate < emergencyThreshold) {
        console.log("⚠️ [AutoPricing] Emergency MR Triggered (" + matchRate + "% < " + emergencyThreshold + "%) -> Fallback to google_optimize");
        return { key: "google_optimize", rule: null };
    }

    var defaultFallback = (fmtName === 'int') ? phpFallbackInt : (fmtName === 'anc') ? phpFallbackAnc : phpFallbackBnr;
    if (!rules || rules.length === 0) return { key: defaultFallback, rule: null };

    var sortedRules = rules.slice().sort(function(a, b) { return a.cpm - b.cpm; });
    var closestIdx = 0;
    var minDiff = Infinity;

    for (var i = 0; i < sortedRules.length; i++) {
        var diff = Math.abs(sortedRules[i].cpm - targetCPM);
        if (diff < minDiff) {
            minDiff = diff;
            closestIdx = i;
        }
    }

    var gap = targetMr - matchRate;
    var chosenIdx = closestIdx;

    if (gap > 10.0) {
        chosenIdx = Math.max(0, closestIdx - 2);
    } else if (gap > 0) {
        chosenIdx = Math.max(0, closestIdx - 1);
    } else {
        chosenIdx = closestIdx;
    }

    var chosenRule = sortedRules[chosenIdx];
    var finalKey = "";

    if (matchRate >= hardFloorMin) {
        finalKey = chosenRule.floor_key || chosenRule.target_key;
    } else {
        finalKey = chosenRule.target_key;
    }

    return { key: finalKey, rule: chosenRule };
}

var userDevice = detectDevice();
var userCountry = window.MBELIK_COUNTRY || 'ID';

var pricingEnginePromise = new Promise(function(resolve) {
    var isResolved = false;

    if (window.MBELIK_INLINE_CURRENT_PRICING && window.MBELIK_INLINE_PRICING_CONFIG) {
        var inlineData = window.MBELIK_INLINE_CURRENT_PRICING;
        var inlineCfg = window.MBELIK_INLINE_PRICING_CONFIG;
        window.mbelikConfig = inlineCfg;

        function computeKeyInline(fmtName) {
            var rawEcpm = 0.0;
            var matchRate = 0.0;
            var fmtLongName = (fmtName === 'bnr') ? 'banner' : (fmtName === 'int') ? 'interstitial' : 'anchor';
            var fmtObj = (inlineCfg.format_settings && inlineCfg.format_settings[fmtLongName]) ? inlineCfg.format_settings[fmtLongName] : {};
            var fmtMultiplier = (fmtObj.multiplier !== undefined) ? fmtObj.multiplier : 1.0;
            var fmtThreshold = (fmtObj.high_mr_threshold !== undefined) ? fmtObj.high_mr_threshold : (inlineCfg.target_mr || 65.0);

            if (inlineData.countries && inlineData.countries[userCountry] && inlineData.countries[userCountry][userDevice]) {
                var cData = inlineData.countries[userCountry][userDevice];
                if (cData[fmtName]) {
                    rawEcpm = cData[fmtName].ecpm || 0.0;
                    matchRate = cData[fmtName].match_rate || 0.0;
                } else {
                    rawEcpm = cData.ecpm || 0.0;
                    matchRate = cData.match_rate || 0.0;
                }
            } else if (inlineData.summary && inlineData.summary[userDevice]) {
                var sData = inlineData.summary[userDevice];
                if (sData[fmtName]) {
                    rawEcpm = sData[fmtName].ecpm || 0.0;
                    matchRate = sData[fmtName].match_rate || 0.0;
                } else {
                    rawEcpm = sData.ecpm || 0.0;
                    matchRate = sData.match_rate || 0.0;
                }
            } else if (inlineData.summary) {
                if (inlineData.summary[fmtName]) {
                    rawEcpm = inlineData.summary[fmtName].ecpm || 0.0;
                    matchRate = inlineData.summary[fmtName].match_rate || 0.0;
                } else {
                    rawEcpm = inlineData.summary.ecpm || 0.0;
                    matchRate = inlineData.summary.match_rate || 0.0;
                }
            }

            var adj = inlineCfg.adjustments || {};
            var deviceMultiplier = 1.0;
            if (inlineCfg.device_settings && inlineCfg.device_settings[userDevice] && inlineCfg.device_settings[userDevice].cpm_multiplier) {
                deviceMultiplier = inlineCfg.device_settings[userDevice].cpm_multiplier;
            }

            var tierMultiplier = 1.0;
            if (adj.high_mr_threshold && matchRate >= adj.high_mr_threshold) {
                tierMultiplier = 1.0 + ((adj.high_mr_boost_pct || 25.0) / 100.0);
            } else if (adj.med_mr_threshold && matchRate >= adj.med_mr_threshold) {
                tierMultiplier = 1.0 + ((adj.med_mr_boost_pct || 10.0) / 100.0);
            } else if (adj.low_mr_threshold && matchRate < adj.low_mr_threshold) {
                tierMultiplier = 1.0 + ((adj.low_mr_penalty_pct || -15.0) / 100.0);
            }

            var adjustedEcpm = rawEcpm * tierMultiplier * deviceMultiplier * fmtMultiplier;
            var targetMr = inlineCfg.target_mr || 65.0;
            var emergencyMrThreshold = inlineCfg.emergency_mr_threshold || 15.0;
            var resRule = findRuleWithStepDown(adjustedEcpm, matchRate, targetMr, inlineCfg.rules || [], emergencyMrThreshold, fmtName, fmtThreshold);

            var defaultFmtFallback = (fmtName === 'int') ? phpFallbackInt : (fmtName === 'anc') ? phpFallbackAnc : phpFallbackBnr;
            var key = (resRule && resRule.key) ? resRule.key : defaultFmtFallback;

            console.log("⚡ [Zero-Fallback AutoPricing] Format:", fmtName, "| Country:", userCountry, "| Device:", userDevice, "| Raw eCPM:", rawEcpm, "| MR:", matchRate + "%", "| Multiplier:", fmtMultiplier, "| Key:", key);
            return key;
        }

        window.pricingEngineResolved = true;
        resolve({ keyBnr: computeKeyInline('bnr'), keyInt: computeKeyInline('int'), keyAnc: computeKeyInline('anc'), config: inlineCfg });
        return;
    }

    var safetyTimer = setTimeout(function() {
        if (!isResolved) {
            isResolved = true;
            window.pricingEngineResolved = true;
            resolve({ keyBnr: phpFallbackBnr, keyInt: phpFallbackInt, keyAnc: phpFallbackAnc, config: null });
        }
    }, 2500);

    Promise.all([
        fetchWithTimeout('/current_pricing.json?t=' + Date.now(), { cache: 'no-store' }, 2000)
            .then(function(res) { return res.ok ? res.json() : null; })
            .catch(function() { return null; }),

        fetchWithTimeout('/pricing_config.json?t=' + Date.now(), { cache: 'no-store' }, 2000)
            .then(function(res) { return res.ok ? res.json() : null; })
            .catch(function() { return null; })
    ])
    .then(function(results) {
        if (isResolved) return;
        isResolved = true;
        window.pricingEngineResolved = true;
        clearTimeout(safetyTimer);

        var pricingData = results[0];
        var config = results[1];

        if (config) window.mbelikConfig = config;

        if (pricingData && config) {
            var targetMr = config.target_mr || 65.0;
            var emergencyMrThreshold = config.emergency_mr_threshold || 15.0;

            function computeKeyAsync(fmtName) {
                var rawEcpm = 0.0;
                var matchRate = 0.0;
                var fmtLongName = (fmtName === 'bnr') ? 'banner' : (fmtName === 'int') ? 'interstitial' : 'anchor';
                var fmtObj = (config.format_settings && config.format_settings[fmtLongName]) ? config.format_settings[fmtLongName] : {};
                var fmtMultiplier = (fmtObj.multiplier !== undefined) ? fmtObj.multiplier : 1.0;
                var fmtThreshold = (fmtObj.high_mr_threshold !== undefined) ? fmtObj.high_mr_threshold : (config.target_mr || 65.0);

                if (pricingData.countries && pricingData.countries[userCountry] && pricingData.countries[userCountry][userDevice]) {
                    var cData = pricingData.countries[userCountry][userDevice];
                    if (cData[fmtName]) {
                        rawEcpm = cData[fmtName].ecpm || 0.0;
                        matchRate = cData[fmtName].match_rate || 0.0;
                    } else {
                        rawEcpm = cData.ecpm || 0.0;
                        matchRate = cData.match_rate || 0.0;
                    }
                } else if (pricingData.summary && pricingData.summary[userDevice]) {
                    var sData = pricingData.summary[userDevice];
                    if (sData[fmtName]) {
                        rawEcpm = sData[fmtName].ecpm || 0.0;
                        matchRate = sData[fmtName].match_rate || 0.0;
                    } else {
                        rawEcpm = sData.ecpm || 0.0;
                        matchRate = sData.match_rate || 0.0;
                    }
                } else if (pricingData.summary) {
                    if (pricingData.summary[fmtName]) {
                        rawEcpm = pricingData.summary[fmtName].ecpm || 0.0;
                        matchRate = pricingData.summary[fmtName].match_rate || 0.0;
                    } else {
                        rawEcpm = pricingData.summary.ecpm || 0.0;
                        matchRate = pricingData.summary.match_rate || 0.0;
                    }
                }

                var adj = config.adjustments || {};
                var deviceMultiplier = 1.0;
                if (config.device_settings && config.device_settings[userDevice] && config.device_settings[userDevice].cpm_multiplier) {
                    deviceMultiplier = config.device_settings[userDevice].cpm_multiplier;
                }

                var tierMultiplier = 1.0;
                if (adj.high_mr_threshold && matchRate >= adj.high_mr_threshold) {
                    tierMultiplier = 1.0 + ((adj.high_mr_boost_pct || 25.0) / 100.0);
                } else if (adj.med_mr_threshold && matchRate >= adj.med_mr_threshold) {
                    tierMultiplier = 1.0 + ((adj.med_mr_boost_pct || 10.0) / 100.0);
                } else if (adj.low_mr_threshold && matchRate < adj.low_mr_threshold) {
                    tierMultiplier = 1.0 + ((adj.low_mr_penalty_pct || -15.0) / 100.0);
                }

                var adjustedEcpm = rawEcpm * tierMultiplier * deviceMultiplier * fmtMultiplier;
                var resRule = findRuleWithStepDown(adjustedEcpm, matchRate, targetMr, config.rules || [], emergencyMrThreshold, fmtName, fmtThreshold);
                var defaultFmtFallback = (fmtName === 'int') ? phpFallbackInt : (fmtName === 'anc') ? phpFallbackAnc : phpFallbackBnr;
                var key = (resRule && resRule.key) ? resRule.key : defaultFmtFallback;

                console.log("🚀 [AutoPricing] Format:", fmtName, "| Country:", userCountry, "| Device:", userDevice, "| Raw eCPM:", rawEcpm, "| MR:", matchRate + "%", "| Multiplier:", fmtMultiplier, "| Key:", key);
                return key;
            }

            resolve({ keyBnr: computeKeyAsync('bnr'), keyInt: computeKeyAsync('int'), keyAnc: computeKeyAsync('anc'), config: config });
            return;
        }

        resolve({ keyBnr: phpFallbackBnr, keyInt: phpFallbackInt, keyAnc: phpFallbackAnc, config: config });
    })
    .catch(function(err) {
        if (!isResolved) {
            isResolved = true;
            window.pricingEngineResolved = true;
            clearTimeout(safetyTimer);
            resolve({ keyBnr: phpFallbackBnr, keyInt: phpFallbackInt, keyAnc: phpFallbackAnc, config: null });
        }
    });
});

var currentDomain = window.location.hostname.replace('www.', '');

googletag.cmd.push(function() {
    var currentUrl = window.location.href;

    googletag.pubads().set('page_url', currentUrl);
    googletag.pubads().setTargeting('domain', currentDomain);
    googletag.pubads().setTargeting('device_type', userDevice);
    googletag.pubads().setTargeting('mbelik_pricing', phpFallbackBnr);

    googletag.pubads().enableLazyLoad({
        fetchMarginPercent: 200,
        renderMarginPercent: 100,
        mobileScalingPercent: 2.0
    });

    var mappingFlexible = googletag.sizeMapping()
        .addSize([1024, 0], [[970, 250], [728, 90]])
        .addSize([0, 0], [[250, 50], [320, 50], [320, 100]])
        .build();

    var mappingFeed = googletag.sizeMapping()
        .addSize([1024, 0], [[300, 250], [336, 280]])
        .addSize([0, 0], [[300, 250], [336, 280]])
        .build();

    slotHeader = googletag.defineSlot('<?php echo isset($phpAdUnits["header"]) ? $phpAdUnits["header"] : $defaultHeader; ?>', [[970, 250], [728, 90], [320, 50], [320, 100], [250, 50]], 'div-gpt-ad-gm-header')
        .defineSizeMapping(mappingFlexible)
        .addService(googletag.pubads());

    slotFeed = googletag.defineSlot('<?php echo isset($phpAdUnits["feed"]) ? $phpAdUnits["feed"] : $defaultFeed; ?>', [[300, 250], [336, 280]], 'div-gpt-ad-gm-feed')
        .defineSizeMapping(mappingFeed)
        .addService(googletag.pubads());

    slotSide1 = googletag.defineSlot('<?php echo isset($phpAdUnits["side1"]) ? $phpAdUnits["side1"] : $defaultSide; ?>', [[300, 250], [300, 600]], 'div-gpt-ad-gm-side1')
        .addService(googletag.pubads());

    slotSide2 = googletag.defineSlot('<?php echo isset($phpAdUnits["side2"]) ? $phpAdUnits["side2"] : $defaultSide2; ?>', [[300, 250], [300, 600]], 'div-gpt-ad-gm-side2')
        .addService(googletag.pubads());

    slotInt = googletag.defineOutOfPageSlot('<?php echo isset($phpAdUnits["interstitial"]) ? $phpAdUnits["interstitial"] : $defaultInt; ?>', googletag.enums.OutOfPageFormat.INTERSTITIAL);
    if (slotInt) {
        slotInt.addService(googletag.pubads());
    }

    slotSticky = googletag.defineOutOfPageSlot('<?php echo isset($phpAdUnits["anchor"]) ? $phpAdUnits["anchor"] : $defaultSticky; ?>', googletag.enums.OutOfPageFormat.BOTTOM_ANCHOR);
    if (slotSticky) {
        slotSticky.addService(googletag.pubads());
    }

    googletag.pubads().enableSingleRequest();
    googletag.pubads().collapseEmptyDivs();
    googletag.enableServices();
});

pricingEnginePromise.then(function(res) {
    var keyBnr = res.keyBnr || phpFallbackBnr;
    var keyInt = res.keyInt || phpFallbackInt;
    var keyAnc = res.keyAnc || phpFallbackAnc;

    window.mbelikPricingVal = keyBnr;

    function applySlotTargeting(slot, slotKey, slotName) {
        if (!slot) return;
        slot.setTargeting('mbelik_pricing', slotKey);
        window.slotStateMap[slotName] = { key: slotKey, state: 'initial' };
        console.log("💰 [AutoPricing SetTargeting] Slot:", slotName, "| Key:", slotKey);
    }

    googletag.cmd.push(function() {
        applySlotTargeting(slotHeader, keyBnr, 'header');
        applySlotTargeting(slotFeed, keyBnr, 'feed');
        applySlotTargeting(slotSide1, keyBnr, 'side1');
        applySlotTargeting(slotSide2, keyBnr, 'side2');
        applySlotTargeting(slotInt, keyInt, 'interstitial');
        applySlotTargeting(slotSticky, keyAnc, 'anchor');
    });
});
</script>
<script>
window.mbelikAccumulator = window.mbelikAccumulator || { sessionTotal: 0 };
window.googletag = window.googletag || { cmd: [] };

googletag.cmd.push(function() {
    googletag.pubads().addEventListener('slotRenderEnded', function(event) {
        var slot = event.slot;
        var isLoaded = !event.isEmpty;

        var path = slot.getAdUnitPath();
        var slotId = slot.getSlotElementId();
        var trackingKey = slotId ? (path + " (" + slotId + ")") : path;

        var targetingValues = slot.getTargeting('mbelik_pricing');
        var pricingKey = (targetingValues && targetingValues.length > 0) ? targetingValues[0] : (window.mbelikPricingVal || 'unknown');

        var isRefreshEligible = (pricingKey !== 'google_optimize');

        var currentRule = null;
        if (window.mbelikConfig && window.mbelikConfig.rules) {
            for (var i = 0; i < window.mbelikConfig.rules.length; i++) {
                var r = window.mbelikConfig.rules[i];
                if (r.target_key === pricingKey || r.floor_key === pricingKey) {
                    currentRule = r;
                    break;
                }
            }
        }

        var estimatedECPM = 0.0;
        if (currentRule && currentRule.cpm) {
            estimatedECPM = currentRule.cpm;
        } else if (pricingKey !== 'unknown' && pricingKey !== 'google_optimize') {
            var numericKey = parseFloat(pricingKey.replace(/[^0-9.]/g, ''));
            if (!isNaN(numericKey) && numericKey > 0) {
                estimatedECPM = numericKey;
            }
        }

        var earning = isLoaded ? (estimatedECPM / 1000.0) : 0.0;

        if (isLoaded) {
            window.mbelikAccumulator.sessionTotal += earning;
        }

        var ecpmFormatted = 'Rp ' + Math.round(estimatedECPM).toLocaleString('id-ID');
        var earningFormatted = isLoaded ? ('+Rp ' + earning.toFixed(2)) : 'Rp 0.00';
        var totalFormatted = 'Rp ' + window.mbelikAccumulator.sessionTotal.toFixed(2);

        var pageUrl = window.location.href;
        var displayUrl = pageUrl.replace(/^https?:\/\//, '');

        var icon = isLoaded ? '💰' : '⚪';
        var statusText = isLoaded ? 'Loaded' : 'Unfilled';

        console.log(
            icon + " [Micro-Earning] Slot: " + trackingKey + " | Status: " + statusText + " | PricingKey: " + pricingKey + " | eCPM: " + ecpmFormatted + " | Earning: " + earningFormatted + " | Total Session: " + totalFormatted + " [" + displayUrl + "]"
        );
    });
});
</script>
"""

cmd = "find /home/mbummm/web/ -type f \( -name 'AdsHeader.php' -o -name 'adsheader.php' \)"
header_files = subprocess.check_output(cmd, shell=True).decode().splitlines()

success = 0
for hf in header_files:
    try:
        with open(hf, 'w') as f:
            f.write(ADS_HEADER_TEMPLATE)
        res = subprocess.check_output(f'php -l {hf}', shell=True).decode()
        if 'No syntax errors detected' in res:
            success += 1
            print(f'PASS: {hf}')
        else:
            print(f'FAIL: {hf} -> {res}')
    except Exception as e:
        print(f'ERROR: {hf} -> {e}')

print(f'\nTOTAL PASSED: {success} / {len(header_files)}')
