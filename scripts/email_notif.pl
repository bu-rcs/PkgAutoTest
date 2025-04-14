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
    ($notif_mlist{$installer}{MSG_HEAD},$notif_mlist{$installer}{FMT_S})=print_header($installer);
}

# header for test result csv:


#,job_number, hostname, qsub_name, test_result,module, tests_passed, tests_failed, log_error_count, exit_code, installer, category, install_date,  workdir
open(R, $test_result_csv) or die "can't open $test_result_csv: $!";
<R>; #skip the first line (header)
while(<R>) {
    chomp;
    $_=~s/\s+//g;
    next if $_ eq ""; #ignore empty lines
    my ($qsub_name, $test_result, $module, $installer, $workdir)=(split /,/)[2,3,4,9,12];
    if( grep {$_ eq $installer} @active_installers ) {
	$notif_mlist{$installer}{MSG_TEXT} .= sprintf($notif_mlist{$installer}{FMT_S}, $installer, $qsub_name, $module,$workdir);
	$notif_mlist{$installer}{FROM} = $installer . "\@bu\.edu";
    }
    else {
	$notif_mlist{$designate_installer}{MSG_TEXT} .= sprintf($notif_mlist{$designate_installer}{FMT_S}, $installer, $qsub_name, $module,$workdir);
	$notif_mlist{$designate_installer}{FROM} = $designate_installer . "\@bu\.edu";
    }
}
close R;

# send emails:
foreach my $installer (keys %notif_mlist) {
    if($notif_mlist{$installer}{MSG_TEXT} ne "") {
	open(MAIL, "|/usr/sbin/sendmail -t") or die "Cannot open sendmail: $!";
	print MAIL "To: $to\n";
	print MAIL "From: $notif_mlist{$installer}{FROM}\n";
	print MAIL "Subject: $installer, please fix the failed tests\n\n";
	print MAIL $notif_mlist{$installer}{MSG_HEAD} . $notif_mlist{$installer}{MSG_TEXT};
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

sub print_header {
    my ($installer) = @_;
    my @colnames=("Installer", "qsub_name", "Module", "WorkDir");
    my @col_minlen=();
    return if(!defined($installer));
    $col_minlen[0]=length($installer)<8?8:length($installer);
    $col_minlen[1]=12;
    $col_minlen[2]=25;
    $col_minlen[3]=30;
    my @sep_str=();
    my @fmt_str=();

    my $delim = " | "; 
    my $fmt_s="";

    for my $i (0..$#colnames) {
	my $col_len=(length($colnames[$i])>$col_minlen[$i])?length($colnames[$i]):$col_minlen[$i];
	push @sep_str,  "-" x $col_len;
	push @fmt_str, "%-" . $col_len . "s";
    }
    $fmt_s = join($delim, @fmt_str) . "\n";

    my $out = sprintf $fmt_s, @colnames;
    $out .= sprintf $fmt_s, @sep_str;
    return ($out, $fmt_s);
}

