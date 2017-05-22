GIT_COMMIT=$(shell git merge-base master HEAD)
GIT_COMMIT_DATE=$(shell git show -s --date=short --format=%cd $(GIT_COMMIT))
PKG_FILE=gassman-$(GIT_COMMIT_DATE)-$(GIT_COMMIT).tgz
TAG_DATE=$(shell date "+%Y-%m-%d-%H_%M")

USER=YOURREMOTEUSER
HOST=YOURREMOTEHOST
PORT=22

build: target/python/gassman_version.py
	gulp build

target/python/gassman_version.py:
	mkdir -p $(@D)
	echo >$@ version=\'$(GIT_COMMIT)\'

deploy:
	./src/main/deploy/tools/deploy_validation.sh
	make dist
	scp -P $(PORT) src/main/deploy/tools/install.sh target/$(PKG_FILE) $(USER)@$(HOST):
	ssh -p $(PORT) $(USER)@$(HOST) ./install.sh $(PKG_FILE) gassman2
	./src/main/deploy/tools/cleanup_hooks.sh
	git tag INSTALLAZIONE_$(TAG_DATE)
	git push
	git push prod INSTALLAZIONE_$(TAG_DATE)

dist: target/$(PKG_FILE)

target/$(PKG_FILE): build
	(cd target/; tar cf dist.tar www)
	(cd src/main/; tar rf ../../target/dist.tar --exclude=__pycache__ deploy python tools tornado_templates translations)
	(cd target/; tar rf dist.tar --exclude=__pycache__ python)
	gzip target/dist.tar
	mv target/dist.tar.gz $@

prepareenv:
	npm install

clean:
	gulp clean
	rm -fR target
	rm -fR `find . -name __pycache__`
	find . -name "*.pyc" -exec rm {} \;
	find . -name "*.pyo" -exec rm {} \;

distclean: clean
	rm -fR node_modules

.PHONY: clean distclean prepareenv dist build deploy target/python/gassman_version.py
