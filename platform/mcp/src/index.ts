import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import express from "express";
import axios from "axios";
import { z } from "zod";

const AI_INFERENCE_URL = process.env.AI_INFERENCE_URL || "http://ai-inference.soc.svc.cluster.local:8000";
const PORT = parseInt(process.env.PORT || "3001", 10);

const app = express();
const server = new McpServer({
    name: "nexus-mcp",
    version: "1.0.0"
});

// Configure MCP Tools

server.tool(
    "query_soc_memory",
    "Query the AI-SOC vector memory for recently triaged security alerts",
    {
        query_text: z.string().describe("The security keywords or entity to search for in memory"),
        limit: z.number().optional().default(3).describe("Number of results to return")
    },
    async ({ query_text, limit }) => {
        try {
            const response = await axios.post(`${AI_INFERENCE_URL}/v1/memory/query`, {
                query_text,
                limit
            });
            return {
                content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }]
            };
        } catch (error: any) {
            return {
                content: [{ type: "text", text: `Error querying memory: ${error.message}` }],
                isError: true
            };
        }
    }
);

server.tool(
    "get_inference_hardware",
    "Scan the inference node for GPU and hardware capabilities",
    {},
    async () => {
        try {
            const response = await axios.get(`${AI_INFERENCE_URL}/v1/hardware`);
            return {
                content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }]
            };
        } catch (error: any) {
            return {
                content: [{ type: "text", text: `Error getting hardware info: ${error.message}` }],
                isError: true
            };
        }
    }
);

server.tool(
    "get_active_models",
    "Get information on active and available AI models in the SOC inference engine",
    {},
    async () => {
        try {
            const response = await axios.get(`${AI_INFERENCE_URL}/v1/models`);
            return {
                content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }]
            };
        } catch (error: any) {
            return {
                content: [{ type: "text", text: `Error getting active models: ${error.message}` }],
                isError: true
            };
        }
    }
);

// Configure Express SSE Routes

let transport: SSEServerTransport;

app.get("/sse", async (req, res) => {
    transport = new SSEServerTransport("/messages", res);
    await server.connect(transport);
});

app.post("/messages", async (req, res) => {
    if (!transport) {
        res.status(400).send("No active SSE connection");
        return;
    }
    await transport.handlePostMessage(req, res);
});

app.listen(PORT, "0.0.0.0", () => {
    console.log(`Nexus MCP Server running on SSE at http://0.0.0.0:${PORT}/sse`);
    console.log(`Connected to AI Inference Engine at: ${AI_INFERENCE_URL}`);
});
