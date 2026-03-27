  To release a new version:                                                                                                                                                      
  1. Update APP_VERSION = '1.x.x' in both index.html and log-sanitizer.html                                                                                                      
  2. Commit: git commit -m "feat: release v1.x.x"                                                                                                                                
  3. Tag: git tag v1.x.x                                                                                                                                                         
                                                                                                                                                                                 
  What's visible in the UI: Zero-Server Sanitizer v1.0.0 appears in the header subtitle under the logo, in both the deployed and portable versions.                              
                                                                                                                                                                                 
  Suggested versioning convention (semver):                                                                                                                                      
  - MAJOR — breaking changes (e.g. data format change)                                                                                                                           
  - MINOR — new features (new rule categories, new profile types)                                                                                                                
  - PATCH — bug fixes  
