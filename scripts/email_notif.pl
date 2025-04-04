#!/usr/bin/env perl

#
#	:  Amanda Yun Shen
#	date:	 01/30/2025
#	purpose: this script get the result.csv from PkgAutoTest and parse it
#                by extracting the failed modules and then send emails to
#                their corresponding installers 
#	usage:   
#         $0 

use 5.010;
use warnings;
use strict;

my $n_arg = scalar(@ARGV);

if ($n_arg != 1) {
    print "USAGE -- \n\temail_notif.pl filepath_failed_test_result.csv\n";
    exit(-1);
}

my ($test_result_csv) = @ARGV;
my @active_installers = get_active_installers(); 
my $designate_installer="bgregor";
my $to=qw(help@scc.bu.edu);

my %notif_mlist = ();

foreach my $installer (@active_installers) {
    $notif_mlist{$installer}{MSG_TEXT}="";
}

# header for test result csv:


#,job_number, hostname, test_result,module, tests_passed, tests_failed, log_error_count, exit_code, installer, category, install_date,  workdir
open(R, $test_result_csv) or die "can't open $test_result_csv: $!";
<R>; #skip the first line (header)
while(<R>) {
    chomp;
    $_=~s/\s+//g;
    my ($test_result, $module, $installer, $workdir)=(split /,/)[3,4,9,12];
    if( grep {$_ eq $installer} @active_installers ) {
	$notif_mlist{$installer}{MSG_TEXT} .= sprintf("%s\t%s\t%s\n", $installer, $module,$workdir);
	$notif_mlist{$installer}{FROM} = $installer . "\@bu\.edu";
    }
    else {
	$notif_mlist{$designate_installer}{MSG_TEXT} .= sprintf("%s\t%s\t%s\n", $installer, $module,$workdir);
	$notif_mlist{$designate_installer}{FROM} = $designate_installer . "\@bu\.edu";
    }
}
close R;

# send emails:
foreach my $installer (keys %notif_mlist) {
#    print "$installer, $notif_mlist{$installer}{MSG_TEXT}";
    if($notif_mlist{$installer}{MSG_TEXT} ne "") {
	open(MAIL, "|/usr/sbin/sendmail -t") or die "Cannot open sendmail: $!";
	print MAIL "To: $to\n";
	print MAIL "From: $notif_mlist{$installer}{FROM}\n";
	print MAIL "Subject: $installer, please fix the failed tests\n\n";
	print MAIL $notif_mlist{$installer}{MSG_TEXT};
	close(MAIL) or warn "sendmail did not close nicely";
    }
    
} #end foreach

print "Emails are all sent!\n\n";


#################################
# SUBROUTINES
#################################
sub get_active_installers{
    my $CMD="grep scv ~scfacct/Project|cut -d: -f1";
    my $output=qx/$CMD/;
    return(split("\n", $output));      
}
