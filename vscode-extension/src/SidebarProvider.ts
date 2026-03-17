import * as vscode from 'vscode';

export class SidebarProvider implements vscode.WebviewViewProvider {
	private _view?: vscode.WebviewView;

	constructor(private readonly _extensionUri: vscode.Uri) {}

	public resolveWebviewView(
		webviewView: vscode.WebviewView,
		_context: vscode.WebviewViewResolveContext,
		_token: vscode.CancellationToken
	) {
		this._view = webviewView;

		webviewView.webview.options = {
			enableScripts: true,
			localResourceRoots: [this._extensionUri],
		};

		webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

		webviewView.webview.onDidReceiveMessage((data) => {
			switch (data.type) {
				case 'onAsk': {
					vscode.commands.executeCommand('codebase-intelligence.askCodebase');
					break;
				}
				case 'onAnalyze': {
					vscode.commands.executeCommand('codebase-intelligence.analyzeCodebase');
					break;
				}
                case 'onImpact': {
					vscode.commands.executeCommand('codebase-intelligence.impactAnalysis');
					break;
				}
                case 'onGetMap': {
                    vscode.commands.executeCommand('codebase-intelligence.getMap');
                    break;
                }
				case 'onError': {
					if (!data.value) return;
					vscode.window.showErrorMessage(data.value);
					break;
				}
			}
		});
	}

	public refresh() {
		if (this._view) {
			this._view.webview.postMessage({ type: 'refresh' });
		}
	}

	public postMessage(message: any) {
		if (this._view) {
			this._view.webview.postMessage(message);
		}
	}

	private _getHtmlForWebview(_webview: vscode.Webview) {
		return `<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<style>
					body { padding: 10px; font-family: var(--vscode-font-family); color: var(--vscode-editor-foreground); }
					.btn { width: 100%; padding: 8px; margin-bottom: 10px; border: none; background: var(--vscode-button-background); color: var(--vscode-button-foreground); cursor: pointer; border-radius: 4px; }
					.btn:hover { background: var(--vscode-button-hoverBackground); }
					.btn-secondary { background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); }
					.btn-secondary:hover { background: var(--vscode-button-secondaryHoverBackground); }
					.card { background: var(--vscode-welcomePage-tileBackground); border: 1px solid var(--vscode-widget-border); padding: 12px; border-radius: 6px; margin-top: 15px; }
					.title { font-weight: 600; margin-bottom: 5px; font-size: 0.9em; opacity: 0.8; }
					.content { white-space: pre-wrap; font-size: 0.85em; line-height: 1.4; color: var(--vscode-descriptionForeground); }
                    pre { background: #010409; padding: 10px; border-radius: 6px; overflow-x: auto; font-family: 'Fira Code', monospace; }
				</style>
			</head>
			<body>
				<div style="margin-bottom: 20px;">
					<h3 style="font-size: 1.1rem; margin-bottom: 15px;">Dashboard</h3>
					<button class="btn" onclick="analyze()">⚡ Analyze Codebase</button>
					<button class="btn btn-secondary" onclick="ask()">💬 Ask a Question</button>
                    <button class="btn btn-secondary" onclick="impact()">🔍 Impact Analysis</button>
                    <button class="btn btn-secondary" onclick="getMap()">🌐 View Project Map</button>
				</div>

				<div id="ai-response-container" style="display: none;">
					<div class="card">
						<div class="title" id="ai-title">AI RESPONSE</div>
						<div class="content" id="ai-content">Thinking...</div>
					</div>
				</div>

				<div id="map-container" style="display: none;">
					<div class="card">
						<div class="title">PROJECT MAP (FILES)</div>
						<div class="content" id="map-content">Loading...</div>
					</div>
				</div>

				<script>
					const vscode = acquireVsCodeApi();

                    function analyze() { vscode.postMessage({ type: 'onAnalyze' }); }
					function ask() { vscode.postMessage({ type: 'onAsk' }); }
                    function impact() { vscode.postMessage({ type: 'onImpact' }); }
                    function getMap() { vscode.postMessage({ type: 'onGetMap' }); }

					window.addEventListener('message', (event) => {
						const message = event.data;
						switch (message.type) {
							case 'ai-response':
								document.getElementById('ai-response-container').style.display = 'block';
								document.getElementById('map-container').style.display = 'none';
								document.getElementById('ai-content').innerText = message.data.answer;
								break;
                            case 'map-data':
								document.getElementById('ai-response-container').style.display = 'none';
								document.getElementById('map-container').style.display = 'block';
                                const files = message.data;
                                document.getElementById('map-content').innerHTML = files.map(f => '<div>📄 ' + f.path + '</div>').join('');
								break;
						}
					});
				</script>
			</body>
			</html>`;
	}
}
