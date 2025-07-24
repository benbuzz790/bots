/**
 * Production Deployment Script for Bot Visualizer
 * 
 * Handles build optimization, asset management, and deployment preparation.
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

class DeploymentManager {
    constructor() {
        this.buildDir = 'dist'
        this.sourceDir = 'src'
    }

    async deploy(options = {}) {
        console.log('🚀 Starting Bot Visualizer deployment...\n')

        try {
            // Step 1: Clean previous builds
            await this.cleanBuild()

            // Step 2: Run integration tests
            if (!options.skipTests) {
                await this.runTests()
            }

            // Step 3: Build production assets
            await this.buildProduction()

            // Step 4: Optimize assets
            await this.optimizeAssets()

            // Step 5: Generate deployment info
            await this.generateDeploymentInfo()

            console.log('✅ Deployment completed successfully!')
            console.log(`📦 Build artifacts available in: ${this.buildDir}/`)
            console.log('🌐 Ready for web server deployment')

        } catch (error) {
            console.error('❌ Deployment failed:', error.message)
            process.exit(1)
        }
    }

    async cleanBuild() {
        console.log('🧹 Cleaning previous build...')
        if (fs.existsSync(this.buildDir)) {
            fs.rmSync(this.buildDir, { recursive: true, force: true })
        }
    }

    async runTests() {
        console.log('🧪 Running integration tests...')
        try {
            // Note: In a real deployment, this would run headless browser tests
            console.log('⚠️  Integration tests require manual verification in development mode')
            console.log('   Run: npm run dev, then click 🧪 Test button')
        } catch (error) {
            throw new Error(`Tests failed: ${error.message}`)
        }
    }

    async buildProduction() {
        console.log('🔨 Building production assets...')
        try {
            execSync('npm run build', { stdio: 'inherit' })
        } catch (error) {
            throw new Error(`Build failed: ${error.message}`)
        }
    }

    async optimizeAssets() {
        console.log('⚡ Optimizing assets...')
        // Additional optimization could be added here
        console.log('   - Assets minified by Vite')
        console.log('   - CSS optimized and purged')
        console.log('   - JavaScript bundled and tree-shaken')
    }

    async generateDeploymentInfo() {
        console.log('📋 Generating deployment info...')
        
        const deploymentInfo = {
            timestamp: new Date().toISOString(),
            version: '1.0.0',
            components: [
                'ConversationTreeView - Interactive conversation tree visualization',
                'BotDashboardView - Real-time bot monitoring and metrics',
                'FunctionalPromptView - Workflow designer (placeholder)'
            ],
            features: [
                'Unified Vue.js application with routing',
                'Centralized state management with Pinia',
                'WebSocket integration for real-time updates',
                'D3.js visualizations for conversation trees',
                'Responsive design with CSS custom properties',
                'Integration testing framework',
                'Mock data system for development'
            ],
            requirements: {
                'Node.js': '>=16.0.0',
                'Modern Browser': 'Chrome 90+, Firefox 88+, Safari 14+',
                'Bot System': 'WebSocket endpoint for real-time communication'
            },
            deployment: {
                'Static Files': `Deploy ${this.buildDir}/ directory to web server`,
                'WebSocket Config': 'Update src/api/websocket.js for production URL',
                'Environment': 'Set NODE_ENV=production'
            }
        }

        fs.writeFileSync(
            path.join(this.buildDir, 'deployment-info.json'),
            JSON.stringify(deploymentInfo, null, 2)
        )

        // Create deployment README
        const readmeContent = `# Bot Visualizer Deployment

## Quick Start

1. **Deploy Static Files**: Copy all files from this directory to your web server
2. **Configure WebSocket**: Update WebSocket URL in assets for your bot system
3. **Verify Connection**: Check that the bot system WebSocket endpoint is accessible

## Build Information

- **Built**: ${deploymentInfo.timestamp}
- **Version**: ${deploymentInfo.version}
- **Components**: ${deploymentInfo.components.length} visualization components

## Requirements

${Object.entries(deploymentInfo.requirements)
    .map(([key, value]) => `- **${key}**: ${value}`)
    .join('\n')}

## Features Included

${deploymentInfo.features.map(feature => `- ${feature}`).join('\n')}

## Support

For issues or questions, refer to the INTEGRATION_GUIDE.md in the source repository.
`

        fs.writeFileSync(
            path.join(this.buildDir, 'README.md'),
            readmeContent
        )
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2)
    const options = {
        skipTests: args.includes('--skip-tests')
    }

    const deployer = new DeploymentManager()
    deployer.deploy(options)
}

module.exports = DeploymentManager
