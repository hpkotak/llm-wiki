# Acme Edge

> Sources: Acme, 2026-09-02
> Raw: [Acme Edge 1.1 release notes](../../raw/products/2026-09-02-acme-edge-1-1.md)
> Updated: 2026-09-05
> Confidence: medium
> Review: discussed 2026-09-06

## Overview

Acme Edge is a runtime for quantized language models on laptops without a discrete GPU. Its 1.1 release added 4-bit weights.

## What we found

Version 1.1 added support for 4-bit weights and cut first-token latency by 18% on Apple M3 machines. The project reports 24K weekly active users, up from 15K in June. Windows on Arm support is planned without a date.

## Relevance

A candidate runtime to evaluate for on-device work on Macs.
