import { NextRequest, NextResponse } from 'next/server';

export async function GET() {
  const API_URL = process.env.API_URL || process.env.LOCAL_APP_URL || 'http://127.0.0.1:8000';
  try {
    // Test connectivity to ADK server using /list-apps endpoint
    const response = await fetch(`${API_URL}/list-apps`, {
      method: 'GET',
    });
    
    if (response.ok) {
      const apps = await response.json();
      return NextResponse.json(
        { 
          status: 'connected', 
          adkServerStatus: response.status,
          message: 'ADK server is reachable',
          availableApps: apps
        },
        {
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
          },
        }
      );
    } else {
      throw new Error(`Server returned ${response.status}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      { 
        status: 'disconnected', 
        error: 'Cannot reach ADK server',
        message: `ADK server is not reachable on ${API_URL}: ${errorMessage}`
      },
      { 
        status: 500,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      }
    );
  }
}
