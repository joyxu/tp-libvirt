import logging
from autotest.client import utils
from autotest.client.shared import error
from virttest import libvirt_xml
from virttest import virsh


def get_processor_version():
    """
    Get host processor version from dmidecode output, return empty list
    if dmidecode command fail.

    :return: the host processor version list
    """
    processer_version = []
    cmd = "dmidecode -t processor | awk -F: '/Version/ {print $2}'"
    cmd_result = utils.run(cmd, ignore_status=True)
    status = cmd_result.exit_status
    output = cmd_result.stdout.strip()
    if not status:
        output_list = output.split('\n')
        for i in output_list:
            processer_version.append(i.strip())
    logging.debug("Processor version list from dmidecode output is: %s"
                  % processer_version)

    return processer_version


def run(test, params, env):
    """
    Test the command virsh sysinfo

    (1) Call virsh sysinfo
    (2) Check result
    """

    option = params.get("virsh_sysinfo_options")
    readonly = "yes" == params.get("readonly", "no")
    status_error = params.get("status_error")

    result = virsh.sysinfo(option, readonly=readonly, ignore_status=True,
                           debug=True)
    output = result.stdout.strip()
    status = result.exit_status

    # Check result
    if status_error == "yes":
        if status == 0:
            raise error.TestFail("Run successfully with wrong command!")
    elif status_error == "no":
        if status != 0:
            raise error.TestFail("Run failed with right command.")
        else:
            dmidecode_version = get_processor_version()
            if dmidecode_version:
                # Get processor version from result
                sysinfo_xml = libvirt_xml.SysinfoXML()
                sysinfo_xml['xml'] = output
                sysinfo_xml.xmltreefile.write()

                processor_version = []
                processor_dict = sysinfo_xml.get_all_processors()
                for i in range(len(processor_dict)):
                    if processor_dict[i].has_key('version'):
                        processor_version.append(processor_dict[i]['version'])
                logging.debug("Processor version list from sysinfo output is: "
                              "%s" % processor_version)

                if processor_version != dmidecode_version:
                    raise error.TestFail("Processor version from sysinfo not"
                                         " equal to dmidecode output")