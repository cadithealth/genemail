=========
ChangeLog
=========


v0.1.12
=======

* Added override of "Message-ID" header to be based on `mailfrom`
  domain (overrideable by setting Email.setHeader or generating in
  template)


v0.1.11
=======

* Added "genemail_format" rendering parameter


v0.1.10
=======

* First tagged release
* Added encryption modifier (using GPG)
* Added defaulting of outbound "Date" header
* Make DKIM modifier support optional
