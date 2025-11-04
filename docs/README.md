# Documentation Index

Welcome to the Multi-Backend Video Generator documentation. This directory contains comprehensive guides for using and understanding the video generation system.

## Quick Links

### Getting Started
- 📖 **[User Guide](user-guide.md)** - Complete user documentation with examples
- 🚀 **[Quick Start](quick-start.md)** - Get up and running in 5 minutes
- 🔧 **[Installation](installation.md)** - Detailed installation instructions

### Backend-Specific Guides
- 🎨 **[OpenAI Sora Guide](backends/openai-sora.md)** - OpenAI Sora-2 setup and usage
- ☁️ **[Azure Sora Guide](backends/azure-sora.md)** - Azure AI Foundry Sora setup
- 🎬 **[Google Veo Guide](backends/google-veo.md)** - Google Veo-3 setup and authentication
- 🎥 **[RunwayML Guide](backends/runwayml.md)** - RunwayML Gen-4 and Veo models

### Advanced Topics
- 🔗 **[Stitching Guide](advanced/stitching.md)** - Multi-clip seamless video generation
- 🖼️ **[Image Grouping Guide](advanced/image-grouping.md)** - Control which images are used per clip
- 📋 **[Image Grouping Quick Reference](advanced/image-grouping-quick.md)** - TL;DR version
- 🎯 **[Prompt Engineering](advanced/prompts.md)** - Writing effective video prompts
- 🛠️ **[Troubleshooting](advanced/troubleshooting.md)** - Common issues and solutions

### Technical Documentation
- 🏗️ **[Architecture](technical/architecture.md)** - System design and structure
- 📚 **[API Reference](technical/api-reference.md)** - Function and class documentation
- 🧪 **[Testing Guide](technical/testing.md)** - Testing strategies and examples
- 📝 **[Development Guide](technical/development.md)** - Contributing and extending

### Reference
- 📊 **[Backend Comparison](reference/backend-comparison.md)** - Feature and pricing comparison
- 🎛️ **[CLI Reference](reference/cli-reference.md)** - Complete command-line reference
- 🔐 **[Authentication](reference/authentication.md)** - All authentication methods
- 🌍 **[Environment Variables](reference/environment-variables.md)** - Configuration reference

## Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── user-guide.md               # Complete user documentation
├── quick-start.md              # Fast getting started guide
├── installation.md             # Installation instructions
│
├── backends/                    # Backend-specific guides
│   ├── openai-sora.md          # OpenAI Sora documentation
│   ├── azure-sora.md           # Azure Sora documentation
│   ├── google-veo.md           # Google Veo documentation
│   └── runwayml.md             # RunwayML documentation
│
├── advanced/                    # Advanced usage topics
│   ├── stitching.md            # Multi-clip video generation
│   ├── image-grouping.md       # Image distribution per clip
│   ├── image-grouping-quick.md # Quick reference for image grouping
│   ├── prompts.md              # Prompt engineering guide
│   └── troubleshooting.md      # Problem solving
│
├── technical/                   # Technical documentation
│   ├── architecture.md         # System architecture
│   ├── api-reference.md        # API documentation
│   ├── testing.md              # Testing guide
│   └── development.md          # Development guide
│
└── reference/                   # Quick reference materials
    ├── backend-comparison.md   # Backend feature comparison
    ├── cli-reference.md        # CLI command reference
    ├── authentication.md       # Authentication methods
    └── environment-variables.md # Environment configuration
```

## About This Project

The Multi-Backend Video Generator is a Python application that converts images to videos using multiple AI backends:
- OpenAI's Sora-2
- Azure AI Foundry Sora-2
- Google's Veo-3
- RunwayML's Gen-4 and Veo models

Key features include:
- ✅ Multi-backend support with unified interface
- ✅ Flexible image input (wildcards, multiple files, mixed formats)
- ✅ Automatic retry logic with exponential backoff
- ✅ Seamless multi-clip stitching (Veo 3.1, RunwayML Veo)
- ✅ Comprehensive logging and error handling
- ✅ Modular, maintainable architecture

## Getting Help

- Check the **[User Guide](user-guide.md)** for comprehensive usage documentation
- See **[Troubleshooting](advanced/troubleshooting.md)** for common issues
- Review **[Examples](user-guide.md#usage-examples)** for practical use cases
- Read **[API Reference](technical/api-reference.md)** for programmatic usage

## Contributing

See the **[Development Guide](technical/development.md)** for information on:
- Setting up a development environment
- Running tests
- Code style and conventions
- Submitting contributions

## License

This project is provided as-is for educational and research purposes.
