# vidb

vidb is a standalone visual debugger for any languages that has a Debug Adapter
Protocol (DAP) that runs on the terminal with a text user interface (TUI).

The user interface and keyboard mapping is heavily inspired by pudb, which was
my favorite Python debugger. If you are used to using pudb or vim, then vidb
should feel right at home.

vidb has only been tested with debugpy but it should work with other debuggers
that supports DAP as well.

# Features

* [ ] attaching to DAP running on TCP port
* [ ] launching new DAP session
* [ ] DAP initialization
* [ ] 
* [ ] master mode

# What's the difference with pudb?

1. vidb is an a DAP client instead of integrating with bdb/pdb. This not
   only allow us to support debugging languages other than Python, but also the
   debugger can more easily take advantage of pydevd/debugpy features instead
   of just bdb.

2. pydevd/debugpy supports debugging not just Python code, but also Django
   templates

3. pydevd/debugpy have better support for debugging code that uses async,
   multithreaded, and subprocesses than bdb/pdb.

4. vidb has first-class support for remote debugging since it is built on top
   of a remote debugging protocol (i.e. DAP), instead of pudb's remote
   debugging which is a hacky bolt on. This also means that vidb UI does not
   need to run on the same terminal as the program being debugged, so vidb does
   not interfere with the stdin/stdout/stderr of the debugee.

5. Windows support for pudb have long been limited due to urwid, vidb is
   written on prompt-toolkit which has better Windows support than urwid.

6. vidb plans to support a Master mode which allows vidb to act as both a DAP
   client and a DAP server. When in Master mode, you can have multiple vidb
   frontends running in multiple terminal or GUI windows being connected to the
   same debugging session.  The vidb master takes care of relay the DAP
   messages to each frontend and synchronizing them into a unified view. This
   allows deeper integration with any IDE and/or text editor that supports
   built-in terminal pane, or with screen/tmux-based workflow, or with
   alternativev vidb frontends.

   - note that vidb's DAP server mode only mostly resembles DAP, but it is not
     fully standard compliant DAP server since it need to support multiple
     simultaneous frontends. Connecting standard DAP client to vidb's DAP
     server port may work, but it is not guaranteed.

# Configuration

## debugpy

https://github.com/microsoft/debugpy/wiki/Debug-configuration-settings
