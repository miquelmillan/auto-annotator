package com.miquelmillan.autoannotator.server;


import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.xmlrpc.webserver.XmlRpcServlet;

public class SemanticServiceProvider extends XmlRpcServlet {
   public SemanticServiceProvider() {
   }

   @Override
   public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
      String extension = request.getRequestURL().substring(request.getRequestURL().length() - 3);
      if (extension.compareTo("owl") == 0)
      {
    	  String URL[] = request.getRequestURL().toString().split("/");
    	  String name = URL[URL.length-1];
    	  java.io.BufferedReader owlFile = new java.io.BufferedReader( new java.io.FileReader (
    			  					this.getServletContext().getRealPath(java.io.File.separatorChar + "owl"
    			  					+ java.io.File.separatorChar+ name))
    	  						);
    	  try {
    		String line;
    		
    	  	while ((line = owlFile.readLine())!=null)
    	  		response.getWriter().write(line+"\n");
    	  	
    	  	owlFile.close();
    	  }catch (IOException e) {
    		  owlFile.close();
    		  System.out.println("Problems managing the owl file: "+e.getMessage());
    	  }
      }	
      else
    	  super.doGet(request,response);
   }
   
   @Override
   public void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
	  System.out.println("doPost()");
      super.doPost(request,response);
   }

   @Override
   public void init(ServletConfig servletConfig ) throws ServletException {
      super.init(servletConfig);
      System.out.println("Startup servlet");
   }

   @Override
   public void destroy() {
      System.out.println("Stopped servlet");
   }

   

}
