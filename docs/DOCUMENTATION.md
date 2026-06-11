# BetterQR Documentation
Welcome to the comprehensive documentation for BetterQR, a powerful and flexible Python library for generating highly customizable QR codes. This document covers everything from installation and basic usage to advanced styling, animation, and data type shortcuts.

## Table of Contents

1.  [Introduction](#introduction)
2.  [Installation](#installation)
3.  [Command-Line Interface (CLI)](#command-line-interface-cli)
    *   [Basic Usage](#basic-usage)
    *   [QR Settings](#qr-settings)
    *   [Styling](#styling)
    *   [Gradients](#gradients)
    *   [Logo Embedding](#logo-embedding)
    *   [Frames & Labels](#frames--labels)
    *   [Animation](#animation)
    *   [Data Type Shortcuts](#data-type-shortcuts)
    *   [Output Options](#output-options)
4.  [Python API](#python-api)
    *   [`QR` Class](#qr-class)
        *   [Initialization](#initialization)
        *   [Styling Methods](#styling-methods)
        *   [Logo Methods](#logo-methods)
        *   [Frame & Label Methods](#frame--label-methods)
        *   [Animation Methods](#animation-methods)
        *   [Output Methods](#output-methods)
        *   [Metadata Properties](#metadata-properties)
    *   [Data Helper Classes](#data-helper-classes)
        *   [`WiFi`](#wifi)
        *   [`VCard`](#vcard)
        *   [`MeCard`](#mecard)
        *   [`GeoLocation`](#geolocation)
        *   [`Event`](#event)
        *   [`SMS`](#sms)
        *   [`Email`](#email)
        *   [`Phone`](#phone)
        *   [`Crypto`](#crypto)
    *   [Batch Generation](#batch-generation)
5.  [Advanced Topics](#advanced-topics)
    *   [Error Correction Levels](#error-correction-levels)
    *   [Transparent Backgrounds](#transparent-backgrounds)
    *   [Logo Sizing and Scannability](#logo-sizing-and-scannability)
6.  [Contributing](#contributing)
7.  [License](#license)

## 1. Introduction

BetterQR is a Python library designed to generate highly customizable QR codes. Unlike many other QR code libraries, BetterQR is built from the ground up in pure Python, meaning it has zero external dependencies for the core QR generation logic. It provides both a convenient command-line interface (CLI) for quick generation and a flexible Python API for programmatic control.

Key features include advanced visual styling options such as custom module shapes, gradient fills, embedded logos, decorative frames, and even animated QR codes. It also simplifies the creation of complex data-type QR codes (e.g., Wi-Fi, vCard) through dedicated helper classes.

## 2. Installation

BetterQR can be easily installed using `pip`:

```bash
pip install betterqr
```

## 3. Command-Line Interface (CLI)

The `betterqr` command provides a rich set of options for generating QR codes directly from your terminal. The basic syntax is:

```bash
betterqr <data> [output_file] [options]
```

If `output_file` is omitted, it defaults to `qr.png`.

### Basic Usage

Generate a simple QR code for a URL:

```bash
betterqr "https://www.example.com" my_qr.png
```

Generate a QR code for plain text:

```bash
betterqr "Hello, BetterQR!" text_qr.png
```

### QR Settings

These options control the fundamental properties of the QR code.