# Mobile — NO-GO for revenue

Audit date: 2026-09-07. Apps live at `AIFromScratch/ios` and `AIFromScratch/android`.

## Verdict
**NO-GO.** Do not ship paid access through the stores until IAP / Play Billing
exist. Apple 3.1.1 and Google Play billing rules still apply. Web checkout from
the apps is not a store-compliant path for unlocking the course.

## iOS
- Native SwiftUI. Paywall links `https://aifromscratch.shop/pago`.
- Free personal team. No `PrivacyInfo.xcprivacy`. No XCTest target.
- Smoke: `ios/run-sim.sh` with `IA_QA_ORIGEN=http://127.0.0.1:4321` when Xcode
  and a simulator are present. Not run in this cycle (time + no store accounts).

## Android
- Compose. No signing config. SDK path may be missing. No JDK was on this Mac
  at plan time (O13: Temurin 17). Emulator smoke BLOCKED without an AVD.

## Owner (O11, O13)
Apple Developer Program, Play Console, IAP vs purchase-free build, JDK if
Android is to be built here.
