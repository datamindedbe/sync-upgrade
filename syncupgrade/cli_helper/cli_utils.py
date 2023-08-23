from typing import Union

from typer import prompt

from syncupgrade.cli_helper.manage_registries import RegistryManager
from syncupgrade.git_integration.git_wrapper import GithubClient
from syncupgrade.models.cli_models import InitOptions, ApplyCommandOptions
from syncupgrade.models.enum_models import ApplyMode


class CliHelper:
    def __init__(self, cli_options: Union[InitOptions, ApplyCommandOptions]):
        self.cli_options = cli_options
        self.git_client = GithubClient() if self.cli_options.activate_git or self.cli_options.remote else None
        self.registry_manager = RegistryManager(self.cli_options,
                                                self.git_client.get_root_path() if self.git_client else None)

    def dry_run(self):
        for refactoring_file_path, refactoring_object in self.registry_manager.get_codmods().items():
            refactoring_object.describe_changes(refactoring_file_path)

    def __apply_code_changes(self):
        for refactoring_file_path, refactoring_object in self.registry_manager.get_codmods().items():
            refactoring_object.apply_code_changes(refactoring_file_path)

    def apply_code(self):
        if not self.cli_options.activate_git:
            self.__apply_code_changes()
            return "Changes applied locally"

        if not self.git_client.check_current_branch(self.cli_options.new_branch_name):
            self.git_client.create_checkout_new_branch(self.cli_options.new_branch_name)
        self.__apply_code_changes()
        if self.cli_options.apply_mode == ApplyMode.pull_request:
            git_token = prompt("Enter your git token", hide_input=True)
            return self.git_client.push_to_remote(self.cli_options, git_token)
        return f"Changes applied locally in branch {self.cli_options.new_branch_name}"

    def process_registries(self):
        if self.cli_options.activate_git:
            self.git_client.create_checkout_new_branch(self.cli_options.new_branch_name)
        if self.cli_options.remote:
            return self.registry_manager.get_remote_registries(
                self.git_client.clone_remote_registries(self.cli_options.registry))
        return self.registry_manager.create_local_registries()
