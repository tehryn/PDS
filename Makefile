.PHONY: zip

zip:
	rm -f xmatej52.zip
	cp doc/xmatej52.pdf dokumentace.pdf
	cp doc/readme readme
	zip xmatej52.zip ConnectionKeeper.py FileLock.py Functions.py InputReader.py pds18-node.py pds18-peer.py pds18-rpc.py Protokol.py Receiver.py Sender.py readme dokumentace.pdf