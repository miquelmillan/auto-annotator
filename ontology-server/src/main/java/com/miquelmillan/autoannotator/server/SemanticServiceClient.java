package com.miquelmillan.autoannotator.server;

import java.net.*;
import org.apache.xmlrpc.client.*;

public class SemanticServiceClient {

	public static void main (String[] args)
	{
		XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();
		try {
			config.setServerURL(new URL("http://127.0.0.1:8080/semantic_services"));
		} catch (Exception e)
		{
			e.printStackTrace();
		}
		XmlRpcClient client = new XmlRpcClient();
		client.setConfig(config);
		Object[] params = new Object[]{"hello", "caca"};
		
		try {
			String result =  (String)client.execute("SemanticServiceProvider.inBound", params);
			System.out.println("The result is: " + result);
		}catch (Exception e){
			e.printStackTrace();
		}
		
	}
	
}


