---
title: react-native-modal-fix
slug: react-native-modal-fix
category: opensource
order: 3
repo: https://github.com/rjrajujha/react-native-modal-fix
demo: https://www.npmjs.com/package/react-native-modal-fix
stack:
  - TypeScript
  - React Native
  - npm
description: Maintained drop-in fork of react-native-modal with production stability fixes.
---

## Problem

Teams on React Native hit upstream gaps in `react-native-modal`: animation glitches across RN versions, keyboard overlap on iOS, and swipe-to-dismiss edge cases. Waiting on upstream releases blocked production fixes.

## Solution

Drop-in replacement preserving the original component API. Platform-specific branches handle keyboard avoidance, safe-area insets, and enter/exit transitions without forcing consumers to change call sites.

## Key Features

- Drop-in API compatibility with upstream
- Keyboard avoidance and safe-area handling on iOS
- Stable animations across React Native minor versions
- Typed exports with MIT license

## Links

- [GitHub](https://github.com/rjrajujha/react-native-modal-fix)
- [npm: react-native-modal-fix](https://www.npmjs.com/package/react-native-modal-fix)
