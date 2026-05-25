/**
 * NeuroGuard - Workflow Engine
 *
 * Lightweight n8n-inspired automation workflow system.
 * Executes node-based pipelines where each node receives input
 * and passes output to the next node in the chain.
 *
 * Architecture:
 *   Workflow → contains ordered Nodes
 *   Node     → receives context, executes logic, returns updated context
 *   Engine   → orchestrates execution, logging, and error handling
 */

// ─── Workflow Registry ─────────────────────────────────────────────────────
const NODE_REGISTRY = {};

/**
 * Register a node handler.
 * @param {string} nodeId   - Unique identifier (e.g. "detect_url")
 * @param {object} config   - { label, description, execute(context) }
 */
function registerNode(nodeId, config) {
  NODE_REGISTRY[nodeId] = {
    id: nodeId,
    label: config.label || nodeId,
    description: config.description || "",
    execute: config.execute,
  };
}

// ─── Workflow Definition ───────────────────────────────────────────────────
const THREAT_DETECTION_WORKFLOW = {
  id: "threat_detection_v2",
  name: "CyberGuard API Threat Detection Pipeline",
  version: "2.0.0",
  description: "Server-side AI and reputation analysis via FastAPI",
  nodes: ["detect_url", "api_scan", "block_website"],
};

// ─── Workflow Execution Engine ─────────────────────────────────────────────
class WorkflowEngine {
  constructor(workflow) {
    this.workflow = workflow;
    this.executionLog = [];
  }

  /**
   * Run the full workflow pipeline.
   * @param {object} initialContext - Starting data (url, tabId, etc.)
   * @returns {object} - Final context after all nodes execute
   */
  async run(initialContext) {
    const startTime = performance.now();
    const executionId = `exec_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

    console.log(`\n╔══════════════════════════════════════════════════════════════╗`);
    console.log(`║  🧠 NeuroGuard Workflow Engine                              ║`);
    console.log(`╠══════════════════════════════════════════════════════════════╣`);
    console.log(`║  Pipeline : ${this.workflow.name.padEnd(46)}║`);
    console.log(`║  Nodes    : ${String(this.workflow.nodes.length).padEnd(46)}║`);
    console.log(`║  Exec ID  : ${executionId.substring(0, 46).padEnd(46)}║`);
    console.log(`╚══════════════════════════════════════════════════════════════╝`);

    let context = {
      ...initialContext,
      _workflow: this.workflow.id,
      _executionId: executionId,
      _startTime: startTime,
      _nodeResults: {},
    };

    this.executionLog = [];
    let aborted = false;

    for (let i = 0; i < this.workflow.nodes.length; i++) {
      const nodeId = this.workflow.nodes[i];
      const node = NODE_REGISTRY[nodeId];

      if (!node) {
        console.error(`  ❌ Node "${nodeId}" not found in registry — skipping`);
        this.executionLog.push({ nodeId, status: "error", error: "Node not registered" });
        continue;
      }

      const stepNum = `[${i + 1}/${this.workflow.nodes.length}]`;
      console.log(`\n  ┌─ ${stepNum} ${node.label}`);
      console.log(`  │  ${node.description}`);

      const nodeStart = performance.now();

      try {
        const result = await node.execute(context);

        // Merge result into context
        if (result && typeof result === "object") {
          context = { ...context, ...result };
          context._nodeResults[nodeId] = { status: "success", data: result, durationMs: performance.now() - nodeStart };
        }

        const duration = (performance.now() - nodeStart).toFixed(0);
        console.log(`  └─ ✔ ${node.label} completed (${duration}ms)`);

        this.executionLog.push({ nodeId, label: node.label, status: "success", durationMs: Number(duration) });

        // Check if a node requests workflow abort
        if (context._abort) {
          console.log(`\n  ⛔ Workflow aborted by node: "${node.label}"`);
          aborted = true;
          break;
        }
      } catch (error) {
        const duration = (performance.now() - nodeStart).toFixed(0);
        console.error(`  └─ ❌ ${node.label} failed (${duration}ms): ${error.message}`);

        context._nodeResults[nodeId] = { status: "error", error: error.message, durationMs: Number(duration) };
        this.executionLog.push({ nodeId, label: node.label, status: "error", error: error.message, durationMs: Number(duration) });
      }
    }

    const totalDuration = (performance.now() - startTime).toFixed(0);

    console.log(`\n╔══════════════════════════════════════════════════════════════╗`);
    console.log(`║  📋 Execution Summary                                       ║`);
    console.log(`╠══════════════════════════════════════════════════════════════╣`);

    for (const log of this.executionLog) {
      const icon = log.status === "success" ? "✔" : "✘";
      const dur = `${log.durationMs}ms`.padStart(8);
      console.log(`║  ${icon} ${log.label.padEnd(40)} ${dur}      ║`);
    }

    console.log(`╠══════════════════════════════════════════════════════════════╣`);
    console.log(`║  Total: ${totalDuration}ms ${aborted ? "| ABORTED" : "| COMPLETE"}${" ".repeat(Math.max(0, 41 - totalDuration.length))}║`);
    console.log(`╚══════════════════════════════════════════════════════════════╝\n`);

    context._totalDurationMs = Number(totalDuration);
    context._executionLog = this.executionLog;

    return context;
  }
}
