import * as vscode from 'vscode';
import axios from 'axios';
import { SidebarProvider } from './SidebarProvider';

export function activate(context: vscode.ExtensionContext) {
	console.log('Congratulations, your extension "codebase-intelligence" is now active!');

    const sidebarProvider = new SidebarProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            "codebaseIntelligenceView",
            sidebarProvider
        )
    );

	// Command: Analyze Codebase
	let analyzeCmd = vscode.commands.registerCommand('codebase-intelligence.analyzeCodebase', async () => {
		const workspaceFolders = vscode.workspace.workspaceFolders;
		if (!workspaceFolders) {
			vscode.window.showErrorMessage('Please open a workspace before analyzing.');
			return;
		}

		const projectPath = workspaceFolders[0].uri.fsPath;
		const apiUrl = vscode.workspace.getConfiguration('codebaseIntelligence').get<string>('apiUrl', 'http://127.0.0.1:8000');

		try {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Analyzing Codebase",
                cancellable: false
            }, async (progress) => {
                progress.report({ message: `Ingesting: ${projectPath}...` });
                const response = await axios.post(`${apiUrl}/api/ingest-repo`, {
                    url: projectPath // Our backend now supports local paths
                });
                
                if (response.status === 200) {
                    vscode.window.showInformationMessage(`Analysis complete! Indexed ${response.data.files_count} files and ${response.data.functions_count} functions.`);
                    sidebarProvider.refresh();
                }
            });
		} catch (error: any) {
			vscode.window.showErrorMessage(`Failed to analyze: ${error.response?.data?.detail || error.message}`);
		}
	});

	// Command: Ask Codebase
	let askCmd = vscode.commands.registerCommand('codebase-intelligence.askCodebase', async () => {
		const question = await vscode.window.showInputBox({ 
			prompt: "Ask a question about your codebase", 
			placeHolder: "What does this project depend on?" 
		});

		if (!question) return;

		const apiUrl = vscode.workspace.getConfiguration('codebaseIntelligence').get<string>('apiUrl', 'http://127.0.0.1:8000');
		
        try {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Thinking...",
                cancellable: false
            }, async () => {
                const response = await axios.post(`${apiUrl}/api/query`, {
                    question: question
                });
                
                if (response.status === 200) {
                    // We can show the result in a simple notification or open the webview
                    vscode.window.showInformationMessage(`AI Response: ${response.data.answer.substring(0, 500)}...`);
                    sidebarProvider.postMessage({ type: 'ai-response', data: response.data });
                    await vscode.commands.executeCommand('codebaseIntelligenceView.focus');
                }
            });
		} catch (error: any) {
			vscode.window.showErrorMessage(`Query failed: ${error.response?.data?.detail || error.message}`);
		}
	});

	// Command: Explain Code
	let explainCmd = vscode.commands.registerCommand('codebase-intelligence.explainCode', async () => {
		const editor = vscode.window.activeTextEditor;
		if (!editor) return;

		const selection = editor.selection;
		const text = editor.document.getText(selection);
		if (!text) return;

        const apiUrl = vscode.workspace.getConfiguration('codebaseIntelligence').get<string>('apiUrl', 'http://127.0.0.1:8000');

        try {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Explaining Selected Code...",
                cancellable: false
            }, async () => {
                const response = await axios.post(`${apiUrl}/api/query`, {
                    question: `Explain what this code does:\n\n${text}`
                });
                
                if (response.status === 200) {
                    sidebarProvider.postMessage({ type: 'ai-response', data: response.data });
                    await vscode.commands.executeCommand('codebaseIntelligenceView.focus');
                }
            });
        } catch (error: any) {
            vscode.window.showErrorMessage(`Explanation failed: ${error.message}`);
        }
	});

    // Command: Impact Analysis
    let impactCmd = vscode.commands.registerCommand('codebase-intelligence.impactAnalysis', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        const filePath = vscode.workspace.asRelativePath(editor.document.uri);
        const apiUrl = vscode.workspace.getConfiguration('codebaseIntelligence').get<string>('apiUrl', 'http://127.0.0.1:8000');

        try {
            const response = await axios.post(`${apiUrl}/api/query`, {
                question: `What are the potential impacts if I change '${filePath}'?`
            });
            sidebarProvider.postMessage({ type: 'ai-response', data: response.data });
            await vscode.commands.executeCommand('codebaseIntelligenceView.focus');
        } catch (error: any) {
            vscode.window.showErrorMessage(`Impact analysis failed: ${error.message}`);
        }
    });

    // Command: Get Map
    let getMapCmd = vscode.commands.registerCommand('codebase-intelligence.getMap', async () => {
        const apiUrl = vscode.workspace.getConfiguration('codebaseIntelligence').get<string>('apiUrl', 'http://127.0.0.1:8000');
        try {
            const response = await axios.get(`${apiUrl}/api/graph/files`);
            sidebarProvider.postMessage({ type: 'map-data', data: response.data });
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to get map: ${error.message}`);
        }
    });

	context.subscriptions.push(analyzeCmd, askCmd, explainCmd, impactCmd, getMapCmd);
}

export function deactivate() {}
