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

$phpSendTo = "AW-16785269892/nNVJCMe5mowaEITJ68M-";
$phpConversionAw = "AW-16785269892";
$cfgJson = null;
if (file_exists($pricingConfigFile)) {
    $cfgContent = @file_get_contents($pricingConfigFile);
    if ($cfgContent) {
        $cfgJson = @json_decode($cfgContent, true);
        if (is_array($cfgJson)) {
            if (isset($cfgJson['ad_units'])) {
                $phpAdUnits = $cfgJson['ad_units'];
            }
            if (isset($cfgJson['conversion']['send_to']) && !empty($cfgJson['conversion']['send_to'])) {
                $phpSendTo = trim($cfgJson['conversion']['send_to']);
                $parts = explode('/', $phpSendTo);
                $phpConversionAw = trim($parts[0]);
            }
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
                else if ($e >= 12000) $phpFallbackBnr = "f12000";
                else if ($e >= 9000)  $phpFallbackBnr = "f9000";
                else if ($e >= 7000)  $phpFallbackBnr = "f7000";
                else if ($e >= 4000)  $phpFallbackBnr = "f4000";
            }
            if (isset($s['int']['ecpm']) && floatval($s['int']['ecpm']) > 0) {
                $e = floatval($s['int']['ecpm']);
                if ($e >= 35000) $phpFallbackInt = "f35000";
                else if ($e >= 30000) $phpFallbackInt = "f30000";
                else if ($e >= 25000) $phpFallbackInt = "f25000";
                else if ($e >= 20000) $phpFallbackInt = "f20000";
                else if ($e >= 15000) $phpFallbackInt = "f15000";
                else if ($e >= 12000) $phpFallbackInt = "f12000";
                else if ($e >= 9000)  $phpFallbackInt = "f9000";
                else if ($e >= 7000)  $phpFallbackInt = "f7000";
                else if ($e >= 4000)  $phpFallbackInt = "f4000";
            }
            if (isset($s['anc']['ecpm']) && floatval($s['anc']['ecpm']) > 0) {
                $e = floatval($s['anc']['ecpm']);
                if ($e >= 30000) $phpFallbackAnc = "f30000";
                else if ($e >= 25000) $phpFallbackAnc = "f25000";
                else if ($e >= 20000) $phpFallbackAnc = "f20000";
                else if ($e >= 15000) $phpFallbackAnc = "f15000";
                else if ($e >= 12000) $phpFallbackAnc = "f12000";
                else if ($e >= 9000)  $phpFallbackAnc = "f9000";
                else if ($e >= 7000)  $phpFallbackAnc = "f7000";
                else if ($e >= 4000)  $phpFallbackAnc = "f4000";
            }
        }
    }
}
?>
<!-- Global site tag (gtag.js) - Google Ads -->
<script data-cfasync="false" async src="https://www.googletagmanager.com/gtag/js?id=<?php echo htmlspecialchars($phpConversionAw); ?>"></script>
<script data-cfasync="false">
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', <?php echo json_encode($phpConversionAw); ?>);
</script>

<script data-cfasync="false">
window.MBELIK_COUNTRY = <?php echo json_encode($detectedCountry); ?>;
window.MBELIK_INLINE_CURRENT_PRICING = <?php echo json_encode($cpJson); ?>;
window.MBELIK_INLINE_PRICING_CONFIG = <?php echo json_encode($cfgJson); ?>;
</script>

<script data-cfasync="false" async src="https://securepubads.g.doubleclick.net/tag/js/gpt.js"></script>
<script data-cfasync="false">
window.googletag = window.googletag || { cmd: [] };

var phpFallbackBnr = <?php echo json_encode($phpFallbackBnr); ?>;
var phpFallbackInt = <?php echo json_encode($phpFallbackInt); ?>;
var phpFallbackAnc = <?php echo json_encode($phpFallbackAnc); ?>;
var phpSendTo = <?php echo json_encode($phpSendTo); ?>;

var slotHeader, slotFeed, slotSide1, slotSide2, slotInt, slotSticky;
window.slotStateMap = window.slotStateMap || {};

function detectDevice() {
    var ua = navigator.userAgent || navigator.vendor || window.opera;
    if (/android/i.test(ua)) return 'mobile';
    if (/iPhone|iPod/i.test(ua)) return 'mobile';
    if (/iPad/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)) return 'mobile';
    return 'desktop';
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

var keys = (function() {
    var inlineData = window.MBELIK_INLINE_CURRENT_PRICING;
    var inlineCfg = window.MBELIK_INLINE_PRICING_CONFIG;
    if (!inlineData || !inlineCfg) {
        return { keyBnr: phpFallbackBnr, keyInt: phpFallbackInt, keyAnc: phpFallbackAnc };
    }
    window.mbelikConfig = inlineCfg;

    function computeKeySync(fmtName) {
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

    return {
        keyBnr: computeKeySync('bnr'),
        keyInt: computeKeySync('int'),
        keyAnc: computeKeySync('anc')
    };
})();

var keyBnr = keys.keyBnr;
var keyInt = keys.keyInt;
var keyAnc = keys.keyAnc;
window.mbelikPricingVal = keyBnr;

var currentDomain = window.location.hostname.replace('www.', '');

googletag.cmd.push(function() {
    var currentUrl = window.location.href;

    googletag.pubads().set('page_url', currentUrl);
    googletag.pubads().setTargeting('domain', currentDomain);
    googletag.pubads().setTargeting('device_type', userDevice);
    googletag.pubads().setTargeting('mbelik_pricing', keyBnr);

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
    slotHeader.setTargeting('mbelik_pricing', keyBnr);

    slotFeed = googletag.defineSlot('<?php echo isset($phpAdUnits["feed"]) ? $phpAdUnits["feed"] : $defaultFeed; ?>', [[300, 250], [336, 280]], 'div-gpt-ad-gm-feed')
        .defineSizeMapping(mappingFeed)
        .addService(googletag.pubads());
    slotFeed.setTargeting('mbelik_pricing', keyBnr);

    slotSide1 = googletag.defineSlot('<?php echo isset($phpAdUnits["side1"]) ? $phpAdUnits["side1"] : (isset($phpAdUnits["side"]) ? $phpAdUnits["side"] : $defaultSide); ?>', [[300, 250], [300, 600]], 'div-gpt-ad-gm-side1')
        .addService(googletag.pubads());
    slotSide1.setTargeting('mbelik_pricing', keyBnr);

    slotSide2 = googletag.defineSlot('<?php echo isset($phpAdUnits["side2"]) ? $phpAdUnits["side2"] : (isset($phpAdUnits["side_2"]) ? $phpAdUnits["side_2"] : $defaultSide2); ?>', [[300, 250], [300, 600]], 'div-gpt-ad-gm-side2')
        .addService(googletag.pubads());
    slotSide2.setTargeting('mbelik_pricing', keyBnr);

    slotInt = googletag.defineOutOfPageSlot('<?php echo isset($phpAdUnits["interstitial"]) ? $phpAdUnits["interstitial"] : $defaultInt; ?>', googletag.enums.OutOfPageFormat.INTERSTITIAL);
    if (slotInt) {
        slotInt.addService(googletag.pubads());
        slotInt.setTargeting('mbelik_pricing', keyInt);
        console.log("💰 [AutoPricing SetTargeting Sync] Slot: interstitial | Key:", keyInt);
    }

    slotSticky = googletag.defineOutOfPageSlot('<?php echo isset($phpAdUnits["anchor"]) ? $phpAdUnits["anchor"] : $defaultSticky; ?>', googletag.enums.OutOfPageFormat.BOTTOM_ANCHOR);
    if (slotSticky) {
        slotSticky.addService(googletag.pubads());
        slotSticky.setTargeting('mbelik_pricing', keyAnc);
        console.log("💰 [AutoPricing SetTargeting Sync] Slot: anchor | Key:", keyAnc);
    }

    googletag.pubads().enableSingleRequest();
    googletag.pubads().collapseEmptyDivs();
    googletag.enableServices();
});
</script>
<script data-cfasync="false">
window.mbelikAccumulator = window.mbelikAccumulator || { sessionTotal: parseFloat(sessionStorage.getItem('mbelik_session_total')) || 0 };
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
        } else if (pricingKey === 'google_optimize') {
            // Option 1: Dynamic Historical JSON eCPM for google_optimize
            var fmtKey = (path.indexOf('play-5') !== -1 || path.indexOf('zse-5') !== -1 || path.indexOf('int') !== -1) ? 'int' : ((path.indexOf('play-6') !== -1 || path.indexOf('zse-6') !== -1 || path.indexOf('anc') !== -1 || path.indexOf('sticky') !== -1) ? 'anc' : 'bnr');
            var cpData = window.MBELIK_INLINE_CURRENT_PRICING || null;
            if (cpData && cpData.summary && cpData.summary[fmtKey] && cpData.summary[fmtKey].ecpm) {
                estimatedECPM = parseFloat(cpData.summary[fmtKey].ecpm) || 0.0;
            }
            if (estimatedECPM <= 0) {
                estimatedECPM = (fmtKey === 'int') ? 25000.0 : (fmtKey === 'anc' ? 10000.0 : 5000.0);
            }
        } else if (pricingKey !== 'unknown') {
            var numericKey = parseFloat(pricingKey.replace(/[^0-9.]/g, ''));
            if (!isNaN(numericKey) && numericKey > 0) {
                estimatedECPM = numericKey;
            }
        }

        var earning = isLoaded ? (estimatedECPM / 1000.0) : 0.0;

        if (isLoaded) {
            window.mbelikAccumulator.sessionTotal += earning;
            try { sessionStorage.setItem('mbelik_session_total', window.mbelikAccumulator.sessionTotal.toFixed(2)); } catch (e) {}
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

    googletag.pubads().addEventListener('impressionViewable', function(event) {
        var slot = event.slot;
        
        // Strict format check: ONLY trigger conversion if the viewable slot is the Interstitial format slot!
        if (typeof slotInt === 'undefined' || slot !== slotInt) return;

        var path = slot.getAdUnitPath();
        var slotId = slot.getSlotElementId();
        var trackingKey = slotId ? (path + " (" + slotId + ")") : path;

        var targetingValues = slot.getTargeting('mbelik_pricing');
        var pricingKey = (targetingValues && targetingValues.length > 0) ? targetingValues[0] : (window.mbelikPricingVal || 'unknown');

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
        } else if (pricingKey === 'google_optimize') {
            var fmtKey = 'int';
            var cpData = window.MBELIK_INLINE_CURRENT_PRICING || null;
            if (cpData && cpData.summary && cpData.summary[fmtKey] && cpData.summary[fmtKey].ecpm) {
                estimatedECPM = parseFloat(cpData.summary[fmtKey].ecpm) || 0.0;
            }
            if (estimatedECPM <= 0) {
                estimatedECPM = 25000.0;
            }
        } else if (pricingKey !== 'unknown') {
            var numericKey = parseFloat(pricingKey.replace(/[^0-9.]/g, ''));
            if (!isNaN(numericKey) && numericKey > 0) {
                estimatedECPM = numericKey;
            }
        }

        var earning = estimatedECPM / 1000.0;

        var activeSendTo = phpSendTo;
        if (window.mbelikConfig && window.mbelikConfig.conversion && window.mbelikConfig.conversion.send_to) {
            activeSendTo = window.mbelikConfig.conversion.send_to;
        } else if (window.MBELIK_INLINE_PRICING_CONFIG && window.MBELIK_INLINE_PRICING_CONFIG.conversion && window.MBELIK_INLINE_PRICING_CONFIG.conversion.send_to) {
            activeSendTo = window.MBELIK_INLINE_PRICING_CONFIG.conversion.send_to;
        }

        var sessionVal = (window.mbelikAccumulator && window.mbelikAccumulator.sessionTotal > 0) ? window.mbelikAccumulator.sessionTotal : earning;

        if (typeof gtag === 'function') {
            gtag('event', 'conversion', {
                'send_to': activeSendTo,
                'value': Number(sessionVal.toFixed(2)),
                'currency': 'IDR'
            });
            console.log("🎯 [Google Ads Interstitial Conversion Sent] Slot: " + trackingKey + " | SendTo: " + activeSendTo + " | Viewable on Screen | Value (Total Session): +Rp " + sessionVal.toFixed(2));
        }
    });
});
</script>
"""

cmd = "sudo find /home/mbummm/web/ -type f \( -name 'AdsHeader.php' -o -name 'adsheader.php' -o -name 'ads-header.php' \) 2>/dev/null"
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
