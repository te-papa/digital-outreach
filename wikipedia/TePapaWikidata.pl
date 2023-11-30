#!/usr/bin/perl -CSDA

# TePapaWikidata.pl
# This script reconciles the Wikidata information with the data in the EMu Parties module.  
# It is supplied for demonstration use and is presented without any warranty.
# The script looks at the EMu data, and then does a live call to Wikidata to get the latest info. It then outputs a csv file with the results.
# Written by Gareth Watkins, Collections Data Manager, Te Papa, 2023.

use utf8;
use strict;
use XML::Simple;
use IO::File;
use JSON;
use LWP::UserAgent;
use POSIX qw(strftime);

sub replaceQuotes {
	#Replace quotes with ', otherwise it may cause formatting issues in the csv output
	my $str = @_[0];
	$str =~ s/\"/'/g;
	return $str;
	}

# Setup variables
my $file;       # File handle
my $out_file;    # CSV File handle
my $out_filename='wikidata-roundtrip-' . time() . '.csv';  

my $xml = XMLin($file,ForceArray=>1);

my $out='';
my $cr = "\r\n"; # Carriage return/newline for output file
my $irn='';
my $tmp_pointer='';
my $tmp_str='';
my $error_flag;
my $wikidata_base_url='https://www.wikidata.org/wiki/'; 
my $user_max=100000; # 100,000 -  the maximum number of records the script will process
my $user_count=0;
my $current_time = time();
my $formatted_date = strftime("%d %b %Y", localtime($current_time));

my %wikidata_q; # Array with info from Wikidata (key = EMu Parties IRN ; value = Wikidata Q)
my %wikidata_label; # Array with info from Wikidata (key = Wikidata Q ; value = Wikidata label)
my %wikidata_web; # Array with info from Wikidata (key = Wikidata Q ; value = Wikidata url)
my %wikidata_q_not_in_emu; # Array with info from wikidata that isn't linked to from EMu (key = EMu Parties IRN ; value = Wikidata Q)
my %wikidata_label_not_in_emu; # Array with info from Wikidata that isn't linked to from EMu (key = Wikidata Q ; value = Wikidata label)
my %emu_q; # Array of EMu records found with a Wikidata identifier (key = EMu Parties IRN ; value = Wikidata Q)
my %emu_label; # Array of EMu records with a display name
my %emu_web; # Array of EMu records found with a Wikidata url (key = EMu Parties IRN ; value = Wikidata Q)
my %irns; # Array of EMu irns (contains the full recordset supplied by the report/xml document)

# Setup column headers
my @col_headers=(
	'Report Response',
	'Parties Irn in EMu',
	'Te Papa Agent ID in Wikidata',
	'Identifer in EMu',
	'Q in Wikidata',
	'Display Name in EMu',
	'Label in Wikidata',
	'Web Associations url in EMu',
	'Wikidata url'
	);

# Main loop to loop through xml from EMu  
foreach my $arg (@{$xml->{tuple}}) {

	if ($arg->{atom}->{irn}->{content} eq '') { next; } # skip if no Parties irn present

	$irn = $arg->{atom}->{irn}->{content};

	$irns{"$irn"}=$irn;

	$tmp_str='';

	if ($arg->{atom}->{NamPartyType}->{content} eq 'Collaboration') {
		if ($arg->{atom}->{ColCollaborationName}->{content}) { $tmp_str = $arg->{atom}->{ColCollaborationName}->{content}; }
		}
	else {
		if ($arg->{atom}->{NamDisplayName}->{content}) { $tmp_str = $arg->{atom}->{NamDisplayName}->{content}; }
		}

	$emu_label{"$irn"}=replaceQuotes($tmp_str);

	$tmp_pointer=0;

	# Identifiers table
	foreach my $tmp_identifiers (@{$arg->{table}->{RolNumberType_tab}->{tuple}}) {
		my $tmp_id='';
		$tmp_id=lc($tmp_identifiers->{atom}->{RolNumberType}->{content});
		if ($tmp_id eq 'wikidata') { 
			my $tmp_q ='';
			$tmp_q= $arg->{table}->{RolNumbersIdentifers_tab}->{tuple}->[$tmp_pointer]->{atom}->{RolNumbersIdentifers}->{content};
			if ($tmp_q ne '') { 
				$emu_q{"$irn"} = $tmp_q; # key = Parties IRN, value = Q number
				} #end if $tmp_q
			} # end if $tmp_id
		$tmp_pointer++;
		} # end foreach $tmp_identifiers

	# Web Associations table
	foreach my $tmp_web (@{$arg->{table}->{AddWebAddress_tab}->{tuple}}) {
		my $tmp_url='';
		$tmp_url=$tmp_web->{atom}->{AddWebAddress}->{content};
		if (lc($tmp_url) =~ /wikidata/) { 
			$emu_web{"$irn"} = $tmp_url; # key = Parties IRN, value = url
			} # end if $tmp_url
		} # end foreach $tmp_web

	$user_count++;
	if ($user_count >= $user_max) { $out.='Maximum number of EMu records (' . $user_max . ') exceeded - script is ending' . $cr ; $error_flag=1; last; }

	} # end main xml loop of EMu data

if (! $error_flag) {
# Query Wikidata for anything that is identified as a Te Papa agent
my $agent = '--SPECIFY A UNIQUE USER AGENT THAT IDENTIFES YOU--'; #see https://w.wiki/CX6

my $query = <<'_SPARQL_QUERY_';
SELECT ?item ?tePapaAgentID ?itemLabel WHERE {
?item wdt:P3544 ?tePapaAgentID .     
SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". } } ORDER BY DESC (?itemLabel)
_SPARQL_QUERY_

my $query_url = "https://query.wikidata.org/sparql?query=${query}&format=json";

my $ua = LWP::UserAgent -> new;
$ua -> agent($agent);
my $req = HTTP::Request -> new(GET => $query_url);
my $res = $ua -> request($req);
my $data = $res -> content;
my $json = decode_json $data;
my $result = $json->{results}->{bindings};

foreach my $key (@$result) {
	my @wikidata_url_split = split('/', $key->{item}->{value});
	my $q_id = pop(@wikidata_url_split);
	my $agent_id = $key->{tePapaAgentID}->{value};
	my $label = replaceQuotes($key->{itemLabel}->{value});
	my $wikidata_url = $key->{item}->{value};
	$wikidata_url =~ s/http:/https:/;  # Replace the "http" Wikidata returns with an "https"
	$wikidata_url =~ s/entity/wiki/; # Replace the "entity" Wikidata returns with "wiki"(on the Wikidata website, /entity/ redirects to /wiki/)

	if (($agent_id ne '') && ($q_id ne '') && ($label ne '' )) { 
			# Add Wikidata url
			$wikidata_web{$q_id} = $wikidata_url;

			# This Q exists in the EMu record set
			if (exists($emu_q{"$agent_id"}) ) {
				$wikidata_q{"$agent_id"} = $q_id;
				$wikidata_label{$q_id} = $label;
				}
			# This Q doesn't exist in the EMu record set
			else {
				$wikidata_q_not_in_emu{"$agent_id"} = $q_id;
				$wikidata_label_not_in_emu{$q_id} = $label;
				}
			} # end if $agent_id

	} # end foreach $key

} # end if $error_flag

# Construct our column headers
$out.='"' . join('","', @col_headers) . '"' . $cr;

# First output the Q identifiers that are found in EMu
foreach my $this_irn (keys %irns) {
	if (exists($wikidata_q_not_in_emu{$this_irn})) { next; } # we ignore ones that aren't linked in EMu.. they appear in the next step
	my @tmp_response;
	my $response='';
	my $this_wikidata_q='';
	my $this_wikidata_q=$wikidata_q{$this_irn}; 
	my $this_w_irn='';
	if ($wikidata_q{$this_irn} ne '') { $this_w_irn=$this_irn; }

	# Do some checks
	if (($emu_q{$this_irn} ne '') && ($wikidata_q{$this_irn} eq '')) { push @tmp_response, 'Not linked in Wikidata back to Te Papa';}
	if (($emu_q{$this_irn} ne '') && ($wikidata_q{$this_irn} ne '') && ($emu_q{$this_irn} ne $wikidata_q{$this_irn} )) { push @tmp_response, 'Wikidata Q mismatch';}
	if (($emu_q{$this_irn} ne '') && ($emu_web{$this_irn} eq '')) { push @tmp_response, 'No EMu Web Association url';}
	if (length($emu_web{$this_irn}) > 50) { push @tmp_response, 'Malformed EMu Web Association url?'; } # eg the url may have been entered twice
	if (@tmp_response) { $response = join(', ', @tmp_response); }
	if (($response eq '') && ($emu_q{$this_irn} eq $wikidata_q{$this_irn}) && ($emu_web{$this_irn} ne '')) {
		$response='Wikidata Q & Web Association url present in EMu';
		}
	# Prepare a row of output data
	my @tmp_row;
	push @tmp_row, $response; # report response
	push @tmp_row, $this_irn;
	push @tmp_row, $this_w_irn;  #agent id found in Wikidata
	push @tmp_row, $emu_q{$this_irn};
	push @tmp_row, $wikidata_q{$this_irn};
	push @tmp_row, $emu_label{$this_irn};
	push @tmp_row, $wikidata_label{$this_wikidata_q};
	push @tmp_row, $emu_web{$this_irn};
	push @tmp_row, $wikidata_web{$this_wikidata_q};
	# Join all data elements together for this row and output. 
	$out.='"' . join('","', @tmp_row) . '"';
	$out.=$cr;

} #end foreach 
	
# Second output the Q identifiers linked in Wikidata that aren't yet found in EMu
foreach my $this_irn (keys %wikidata_q_not_in_emu) {
	my $this_wikidata_q='';
	my $response='';
	$this_wikidata_q=$wikidata_q_not_in_emu{$this_irn}; 
	if (exists($irns{$this_irn})) { $response='Not linked in EMu back to Wikidata'; } else { $response='EMu Parties record not found (not in search or does not exist)';}

	# Prepare a row of output data
	my @tmp_row;
	push @tmp_row, $response; # Report response
	push @tmp_row, ''; # This irn in EMu
	push @tmp_row, $this_irn;  # Agent id found in Wikidata
	push @tmp_row, $emu_q{$this_irn}; # This Q in EMu
	push @tmp_row, $wikidata_q_not_in_emu{$this_irn};
	push @tmp_row, $emu_label{$this_irn}; # This label in EMu
	push @tmp_row, $wikidata_label_not_in_emu{$this_wikidata_q};
	push @tmp_row, $emu_web{$this_irn};
	push @tmp_row, $wikidata_web{$this_wikidata_q};
	$out.='"' . join('","', @tmp_row) . '"';
	$out.=$cr;
	}

# Print a BOM Byte Order Mark at the front of the file.  Not necessary for UTF-8, but Windows Excel won't interpret the unicode characters correctly if it is not present
print $out_file chr(65279); 

# Output the data
print $out_file $out;

# Tell EMu the output filename to launch
print("$out_filename\n");

$out_file->close();

# All done, exit
exit(0);
