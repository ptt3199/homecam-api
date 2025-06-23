# 📚 HomeCam API Documentation

This folder contains technical analysis and documentation for the HomeCam API project.

## 📁 **Folder Structure**

```
docs/
├── README.md                           # This file
├── analysis/                          # Code analysis reports
│   └── code_analysis_summary.md       # Vulture & Pyflakes analysis
└── auth/                             # Authentication documentation
    ├── clerk_jwt_analysis.md          # Clerk JWT verification process
    └── token_comparison_analysis.md   # Clerk vs Streaming tokens
```

## 📋 **Documentation Index**

### 🔍 **Code Analysis** (`analysis/`)
- **`code_analysis_summary.md`** - Comprehensive unused code analysis using Vulture and other tools
  - Dead code detection results
  - Unused imports analysis
  - Cleanup recommendations

### 🔐 **Authentication** (`auth/`)  
- **`clerk_jwt_analysis.md`** - Detailed analysis of Clerk JWT verification process
  - JWT structure and claims
  - JWKS dynamic fetching
  - Verification flow
- **`token_comparison_analysis.md`** - Comparison between Clerk tokens and streaming tokens
  - Main authentication vs streaming tokens
  - Lifetime and security differences
  - Auto-renewal mechanisms

## 🛠️ **Tools Used**
- **Vulture** - Dead code detection
- **Pyflakes** - Unused imports detection  
- **Manual Code Review** - Architecture and flow analysis

## 📁 **Organization Rule**
All technical analysis, documentation, and reports should be placed in this `docs/` folder with appropriate subdirectories to keep the project root clean and organized.

## 🔗 **Quick Links**
- [Code Analysis Summary](./analysis/code_analysis_summary.md)
- [Clerk JWT Analysis](./auth/clerk_jwt_analysis.md) 
- [Token Comparison](./auth/token_comparison_analysis.md) 